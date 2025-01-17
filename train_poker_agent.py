# FILE: agent.py

from stable_baselines3 import PPO
from ProbabilityStatesEnv import BountyHoldemEnv
from stable_baselines3 import A2C, PPO
import os
import gymnasium as gym
import numpy as np

models_dir = "models/poker-realppo-llast"
log_dir = "logs/poker-realppo-llast"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

env = BountyHoldemEnv()
model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_dir, ent_coef=0.005, gae_lambda=0, batch_size=250, n_epochs=200)

TIMESTEPS = 1000
for i in range(1, 3000000):
    print(i)
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name="PPO")
    model.save(f"{models_dir}/{TIMESTEPS * i}")

episodes = 100

'''
for ep in range(episodes):
    obs, _ = env.reset()
    done = False
    while not done:
        env.render()
        action = int(input("Enter action: "))
        obs, reward, done, trunc, info = env.step(action)
        print("Reward:",reward)


env.close()'''









