# FILE: agent.py

from stable_baselines3 import PPO
from ProbabilityStatesEnv import BountyHoldemEnv
from siamese_policy import SiamesePolicy
import gymnasium as gym


env = BountyHoldemEnv()

episodes = 5

for ep in range(episodes):
    obs, _ = env.reset()
    print(obs)
    done = False
    while not done:
        env.render()
        action = int(input("Enter action: "))
        obs, reward, done, trunc, info = env.step(action)
        print("Reward:",reward)
        print(obs)


env.close()