"""GET /goals and POST /goals/{id}/toggle."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from db import SessionDep
from models import Goal, GoalOut

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=List[GoalOut])
async def list_goals(session: SessionDep) -> List[Goal]:
    return list(session.exec(select(Goal).order_by(Goal.due_date, Goal.id)).all())


@router.post("/goals/{goal_id}/toggle", response_model=GoalOut)
async def toggle_goal(goal_id: int, session: SessionDep) -> Goal:
    goal = session.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found.")
    goal.is_completed = not goal.is_completed
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal
