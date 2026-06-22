from __future__ import annotations
from pathlib import Path
from .env import RescueOperatorEnv
from .config import Settings

def train_ppo(output: str="models/ppo_rescue", timesteps:int=1000, seed:int=42):
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.callbacks import CheckpointCallback
    except Exception as exc:
        raise RuntimeError("stable-baselines3 is required for PPO training") from exc
    env=make_vec_env(lambda: RescueOperatorEnv(Settings(seed=seed)), n_envs=2, seed=seed)
    model=PPO("MlpPolicy", env, seed=seed, verbose=0)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    model.learn(total_timesteps=timesteps, callback=CheckpointCallback(save_freq=500, save_path=str(Path(output).parent)))
    model.save(output); return output
