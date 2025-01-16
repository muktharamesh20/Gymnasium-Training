import gym
from stable_baselines3 import PPO
import numpy

env = gym.make("LunarLander-v2", render_mode="human")
env.reset()

models_dir = "models/PPO-7"
model_path = f"{models_dir}/530000" 

model = PPO.load(model_path, env=env)

episodes = 100

for ep in range(episodes):
    obs, _ = env.reset()
    done = False
    while not done:
        env.render()
        action, _ = model.predict(obs)
        obs, reward, done, trunc, info = env.step(action)

env.close()