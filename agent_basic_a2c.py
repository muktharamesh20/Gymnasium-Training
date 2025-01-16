import gym
from stable_baselines3 import A2C, PPO
import os

models_dir = "models/A2C"
log_dir = "logs/A2C"

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

env = gym.make("LunarLander-v2")
env.reset()

model = A2C("MlpPolicy", env, verbose=1, tensorboard_log=log_dir)

TIMESTEPS = 100000
for i in range(1, 30):
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name="A2C")
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