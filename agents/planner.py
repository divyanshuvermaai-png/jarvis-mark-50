"""
J.A.R.V.I.S. Planner Agent
Decomposes complex user objectives into structured, dependency-aware TaskGraphs.
"""
import json
import re
from typing import List, Dict, Any, Optional
from .base import BaseAgent
from core.task_manager import Task, SubTask, TaskGraph, TaskStatus

class PlannerAgent(BaseAgent):
    def __init__(self, router, tools=None, procedural_memory=None):
        super().__init__(
            name="PlannerAgent",
            role="Objective Decomposition & Strategic Task Planning",
            router=router,
            tools=tools
        )
        self.procedural_memory = procedural_memory


    @property
    def system_prompt(self) -> str:
        available_tools = [f"- {t.id}: {t.description}" for t in self.tools.list_tools()]
        tools_str = "\n".join(available_tools)
        return f"""You are the strategic PLANNING AGENT of J.A.R.V.I.S.
Your mission is to decompose the user's objective into an ordered JSON list of execution steps.

AVAILABLE TOOLS:
{tools_str}

OUTPUT REQUIREMENTS:
Return ONLY a valid JSON array of objects. No markdown formatting, no explanations.
Schema for each element:
{{
  "id": "step1",
  "title": "Short title",
  "description": "What to accomplish",
  "tool_hint": "tool_id or null",
  "tool_params": {{"param": "value"}},
  "dependencies": []
}}

Rules:
1. Max 5 steps.
2. For conversational queries or direct knowledge questions that require no tools, return:
   [{{"id": "step1", "title": "Respond conversationally", "description": "Formulate answer", "tool_hint": null, "tool_params": {{}}, "dependencies": []}}]
3. Keep dependencies topological (e.g. step2 may depend on ["step1"])."""

    def plan(self, task: Task) -> TaskGraph:
        task.mark_status(TaskStatus.PLANNING)
        graph = TaskGraph(task)

        # 1. Procedural Memory Shortcut (Fast-path proven recipes)
        if self.procedural_memory:
            proc = self.procedural_memory.find_matching_procedure(task.objective)
            if proc and proc.get("steps"):
                task.artifacts["matched_procedure_id"] = proc["id"]
                prev_step_id = None
                for idx, step in enumerate(proc["steps"]):
                    sid = f"step_{idx+1}"
                    st = SubTask(
                        id=sid,
                        title=str(step.get("step_name", f"Step {idx+1}")),
                        description=str(step.get("description", f"Execute {step.get('tool')}")),
                        tool_hint=step.get("tool"),
                        tool_params=step.get("params", {}),
                        dependencies=[prev_step_id] if prev_step_id else []
                    )
                    graph.add_subtask(st)
                    prev_step_id = sid

                graph.validate()
                task.mark_status(TaskStatus.READY)
                return graph

        prompt = f"Objective to plan: {task.objective}"
        try:
            raw_response, selected_provider = self.router.execute(

                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=800,
                temperature=0.2
            )
            
            # Clean possible markdown wrapping
            clean_json = re.sub(r"^```\w*\n?", "", raw_response.strip())
            clean_json = re.sub(r"\n?```$", "", clean_json).strip()

            # Attempt JSON parsing
            steps_data = json.loads(clean_json)
            if isinstance(steps_data, list) and len(steps_data) > 0:
                for idx, step in enumerate(steps_data):
                    st = SubTask(
                        id=str(step.get("id", f"step_{idx+1}")),
                        title=str(step.get("title", f"Step {idx+1}")),
                        description=str(step.get("description", "")),
                        tool_hint=step.get("tool_hint"),
                        tool_params=step.get("tool_params", {}),
                        dependencies=step.get("dependencies", [])
                    )
                    graph.add_subtask(st)
                
                graph.validate()
                task.mark_status(TaskStatus.READY)
                return graph

        except Exception as e:
            # Fallback: simple 1-step plan
            pass

        # Resilient fallback plan
        single_step = SubTask(
            id="step_1",
            title="Execute Objective",
            description=task.objective,
            tool_hint=None,
            tool_params={},
            dependencies=[]
        )
        graph.add_subtask(single_step)
        task.mark_status(TaskStatus.READY)
        return graph
