from alphaapollo.core.environments.informal_math_training.base_text_env import BaseTextEnv, BaseTextEnvStepOutput, ConversationType
from typing import Any
from alphaapollo.core.environments.informal_math_training.utils.qwen_math import compute_score, extract_answer_segment
from alphaapollo.core.tools.manager import InformalMathToolGroup
from typing import Dict, Optional, List, Tuple
from omegaconf import DictConfig

from alphaapollo.core.environments.informal_math_training.skill_bridge import (
    ParsedToolAction,
    execute_skill_call_with_tool_group,
    parse_tool_actions,
    tool_error_response,
    wrap_tool_response,
)
from alphaapollo.core.skills.registry import (
    get_builtin_skill_dirs,
    load_skill_registry_from_dirs,
    resolve_enabled_skill_names,
)

class InformalMathTrainingEnv(BaseTextEnv):
    """
    Environment for Informal Math tasks.
    """

    def __init__(self, env_config: DictConfig):
        super().__init__()
        enabled_skills = resolve_enabled_skill_names(env_config, env_section="informal_math_training")
        explicit_skills = _get_config_value(env_config, "skills", None) is not None
        if explicit_skills:
            enable_python_code = "python_code" in enabled_skills
            enable_local_rag = "local_rag" in enabled_skills
        else:
            enable_python_code = _get_config_value(env_config, "enable_python_code", True)
            enable_local_rag = _get_config_value(env_config, "enable_local_rag", True)
        
        # Build tool_config dict for tool group initialization
        tool_config = {
            "enable_python_code": enable_python_code,
            "enable_local_rag": enable_local_rag,
            "python_code_timeout": _get_config_value(env_config, "python_code_timeout", 30),
            "rag_cfg": _get_config_value(env_config, "rag", None),
        }
        
        # Initialize the tools
        self.tool_group = InformalMathToolGroup(
            log_requests=getattr(env_config, "log_requests", False),
            vllm_cfg=getattr(env_config, "vllm", None),
            verifier_cfg=getattr(env_config, "verifier", None),
            tool_config=tool_config,
        )
        self.init_tool_groups([self.tool_group])

        enabled_registry_result = load_skill_registry_from_dirs(
            get_builtin_skill_dirs(),
            enabled_skills=enabled_skills,
        )
        if enabled_registry_result.errors:
            formatted_errors = "; ".join(f"{error.code}: {error.message}" for error in enabled_registry_result.errors)
            raise ValueError(f"Failed to load enabled skills: {formatted_errors}")
        registry_result = load_skill_registry_from_dirs(get_builtin_skill_dirs())
        if registry_result.errors:
            formatted_errors = "; ".join(f"{error.code}: {error.message}" for error in registry_result.errors)
            raise ValueError(f"Failed to load built-in skills: {formatted_errors}")
        self.skill_registry = registry_result.registry
        self.enabled_skill_names = enabled_registry_result.loaded

    def reset(self, extras: Optional[Dict[str, Any]] = None) -> None:
        # NOTE: using the information in "extra_info" of the data field to initialize the environment
        extras = extras or {}
        for key in ["question", "ground_truth"]:
            assert key in extras, f"{key} is required in extras field"

        self.question = extras["question"]
        # self.gt_traj = extras.get("gt_traj", None)
        self.ground_truth = extras["ground_truth"]
        self.max_steps = extras.get("max_steps", 3)
        self.data_source = extras.get("data_source", "unknown")

        # Set ground truth in tool group for Python verification
        self.tool_group.set_ground_truth(self.ground_truth)

        # Chat history
        # role (user, assistant), content (tool observation or LLM response)
        self.chat_history: ConversationType = []
        self.done = False
        self.turns = 0
        self._score_list = []

    def _get_reward(self, done: bool) -> float:
        if done:
            # Concat all chat history into a single string and compute reward
            chat_history_str = "".join([item["text_actions"] for item in self.chat_history])
            solution_str = chat_history_str

            return compute_score(solution_str=solution_str, ground_truth=self.ground_truth)
        else:
            # No reward for intermediate steps for Informal Math tasks
            return 0
    
    
    def _is_done(self, tool_calls: List[ParsedToolAction]) -> bool:
        # 1. exceed max steps
        if self.turns >= self.max_steps:
            return True
        
        # 2. no tool calls
        if not tool_calls or all(not tool_call.is_tool_action for tool_call in tool_calls):
            return True

        return False

    def _execute_tool(self, tool_group_name: str, tool_name: str, tool_inputs: Any, return_score: bool = False) -> Any:
        tool_output = super()._execute_tool(tool_group_name, tool_name, tool_inputs)
        text_result = tool_output.get("text_result", "")
        score = tool_output.get("score", None)
        if return_score:
            return "\n<tool_response>" + text_result + "</tool_response>\n", score
        else:
            return "\n<tool_response>" + text_result + "</tool_response>\n"

    def _parse_action(self, action: str) -> List[ParsedToolAction]:
        """
        Parse action to extract structured or legacy tool calls.
        """
        return parse_tool_actions(action, registry=self.skill_registry)

    def _execute_skill_tool_action(self, parsed_action: ParsedToolAction) -> Tuple[Optional[str], Dict[str, Any]]:
        tool_name = parsed_action.tool_name
        tool_input = parsed_action.tool_input

        tool_info = {
            "tool_calling": True,
            "tool_group": "InformalMathToolGroup",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_call_format": parsed_action.call_format,
            "data_source": self.data_source,
        }

        if parsed_action.legacy_error_response is not None:
            tool_info["error"] = parsed_action.error.code if parsed_action.error else "legacy_error"
            return wrap_tool_response(parsed_action.legacy_error_response), tool_info

        if parsed_action.error is not None:
            tool_info["error"] = parsed_action.error.code
            return wrap_tool_response(tool_error_response(parsed_action.error)), tool_info

        if parsed_action.call is None:
            return None, tool_info

        result = execute_skill_call_with_tool_group(
            parsed_action.call,
            self.skill_registry,
            self.tool_group,
        )
        tool_info["tool_name"] = result.tool_name
        tool_info["tool_input"] = parsed_action.call.arguments
        tool_info["score"] = result.score
        if result.error is not None:
            tool_info["error"] = result.error.code

        return wrap_tool_response(result.text_result), tool_info

    def step(self, action: StopIteration, text_actions: List[str]) -> BaseTextEnvStepOutput:
        self.turns += 1
        self.chat_history.append({"role": "assistant", 
                                  "content": action, 
                                  "text_actions": text_actions
                                  })

        # parse action to tool calls
        # NOTE: Use text_actions (original model output) instead of action (projection-truncated)
        # to correctly extract ALL tool calls including local_rag when multiple tools are enabled
        raw_action = text_actions if isinstance(text_actions, str) else action
        try:
            tool_calls = self._parse_action(raw_action)
        except Exception as e:
            raise Exception(f"Error parsing action: {e}, action: {raw_action}")
        
        self.done = self._is_done(tool_calls)

        reward = self._get_reward(self.done)

        if self.done:
            return BaseTextEnvStepOutput(
                observations=[],
                reward=reward,
                done=self.done,
                metadata={"data_source": self.data_source, "tool_calling": False},
                postprocessed_action=action
            )


        observations = []
        tool_infos = []
        
        for tool_call in tool_calls:
            if tool_call.is_tool_action:
                observation = None
                tool_info = None
                tool_name = tool_call.tool_name
                tool_input = tool_call.tool_input
                
                if tool_name == "informalmath_verify":
                    observation = self._execute_tool(
                        "InformalMathToolGroup",
                        "informalmath_verify",
                        {
                            "question": self.question,
                            "solution": tool_input,
                        },
                    )
                    tool_info = {
                        "tool_calling": True,
                        "tool_group": "InformalMathToolGroup",
                        "tool_name": "informalmath_verify",
                        "tool_input": tool_input,
                        "tool_call_format": tool_call.call_format,
                        "data_source": self.data_source,
                    }
                else:
                    observation, tool_info = self._execute_skill_tool_action(tool_call)

            # Wrap the observation properly as a message
            if observation:
                new_obs = {"role": "user", "content": observation, "text_actions": text_actions}
                self.chat_history.append(new_obs)
            else:
                new_obs = None
            if tool_info is None:
                tool_info = {
                    "tool_calling": False,
                    "tool_group": "InformalMathToolGroup",
                    "tool_name": None,
                    "tool_input": None,
                    "data_source": self.data_source,
                    }
            observations.append(new_obs)
            tool_infos.append(tool_info)


        return BaseTextEnvStepOutput(
            observations=observations,
            reward=reward,
            done=self.done,
            metadata=tool_infos,
            postprocessed_action=action,
        )


def _get_config_value(config: Any, key: str, default: Any = None) -> Any:
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)
