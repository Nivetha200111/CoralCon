"""Notion property templates for CoralCon action tasks."""


def build_task_properties(task: dict) -> dict:
    return {
        "Title": {"title": [{"text": {"content": task["title"][:1900]}}]},
        "Priority": {"select": {"name": task.get("priority", "Medium")}},
        "Deadline": {"date": {"start": task.get("deadline")}},
        "Category": {"select": {"name": task.get("category", "application_strategy")}},
        "Impact": {"rich_text": [{"text": {"content": task.get("impact", "")[:1900]}}]},
        "Status": {"select": {"name": task.get("status", "Not Started")}},
    }
