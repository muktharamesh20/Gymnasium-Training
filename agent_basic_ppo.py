import gym
from stable_baselines3 import A2C, PPO
import os

models_dir = "models/PPO-15"
log_dir = "logs/PPO-15"

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

env = gym.make("LunarLander-v2")
env.reset()

model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_dir, learning_rate=0.0003, ent_coef=0.02)

TIMESTEPS = 100000
for i in range(1, 300):
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name="PPO")
    model.save(f"{models_dir}/{TIMESTEPS * i}")

episodes = 100

'''
for ep in range(episodes):
    obs = env.reset()
    done = False

    while not done:
        env.render()
        obs,reward,done, truncated, info = env.step(env.action_space.sample())
        print(reward)

env.close()'''