# FILE: agent.py

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from Environment import BountyHoldemEnv
import os
import gymnasium as gym
import numpy as np

models_dir = "models/masked-self-play-10k-not-scratch"
log_dir = "logs/masked_-self-play-10k-not-scratch"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def mask_fn(env: gym.Env):
    return env.get_legal_action_mask()

env = BountyHoldemEnv()
env = ActionMasker(env, mask_fn)
#model = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1, tensorboard_log=log_dir, ent_coef=0.01)
model = MaskablePPO.load("models/masked_nenv-ent1-10k/1490000", env=env)



TIMESTEPS = 10000
for i in range(1, 3000000):
    print(i)
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name="self-play-10k-not-scratch")
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









