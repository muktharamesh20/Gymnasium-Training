import gym
from stable_baselines3 import PPO
from Environment import BountyHoldemEnv
import numpy
import time

env = BountyHoldemEnv()
env.reset()

models_dir = "models/masked_nenv-ent1-10k"
model_path = f"{models_dir}/1490000" 

model = PPO.load(model_path, env=env)

episodes = 100

for ep in range(episodes):
    obs, _ = env.reset()
    done = False
    while not done:
        #env.render()
        action, _ = model.predict(obs)
        valid_actions = []
        for index, i in enumerate(obs[9:, 0]):
            if i == 1:
                valid_actions.append(index)
        print("Valid Actions", valid_actions)
        print("Chosen Action", action)
        obs, reward, done, trunc, info = env.step(action)
        print("Reward", reward)
        time.sleep(5)


env.close()