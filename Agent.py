# FILE: agent.py

from stable_baselines3 import PPO
from Environment import BountyHoldemEnv
from siamese_policy import SiamesePolicy
import gymnasium as gym

class Agent:
    def __init__(self, environment):
        self.env = BountyHoldemEnv()
        self.model = PPO(SiamesePolicy, self.env, verbose=1)

    def train(self, timesteps=10000):
        self.model.learn(total_timesteps=timesteps)

    def choose_action(self, state):
        action, _ = self.model.predict(state)
        return action

    def play_round(self):
        state = self.environment.get_state()
        action = self.choose_action(state)
        self.environment.perform_action(action)
        result = self.environment.evaluate_hands()
        self.environment.handle_round_end(result)
        return result

'''
env = BountyHoldemEnv()
agent = Agent(env)
agent.train(timesteps=10000)
result = agent.play_round()
print(f"Round result: {result}")'''

env = BountyHoldemEnv()

episodes = 1

for ep in range(episodes):
    obs, _ = env.reset()
    done = False
    while not done:
        env.render()
        action = int(input("Enter action: "))
        obs, reward, done, trunc, info = env.step(action)
        print("Reward:",reward)

env.close()