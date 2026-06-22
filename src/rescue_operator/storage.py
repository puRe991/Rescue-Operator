from __future__ import annotations
import sqlite3
from pathlib import Path
from .models import GameState, DecisionRecord

class SQLiteStore:
    def __init__(self, path: str="runs/rescue_operator.sqlite"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn=sqlite3.connect(self.path)
        self.conn.execute("create table if not exists states(time_minute integer primary key, json text not null)")
        self.conn.execute("create table if not exists decisions(id integer primary key autoincrement, time_minute integer, json text not null)")
    def save_state(self,state:GameState):
        # Persist periodic checkpoints to keep long autonomous runs bounded.
        if state.time_minute % 60 != 0:
            return
        self.conn.execute("insert or replace into states values(?,?)", (state.time_minute, state.model_dump_json())) ; self.conn.commit()
    def save_decision(self,record:DecisionRecord):
        self.conn.execute("insert into decisions(time_minute,json) values(?,?)", (record.time_minute, record.model_dump_json())) ; self.conn.commit()
    def close(self): self.conn.close()
