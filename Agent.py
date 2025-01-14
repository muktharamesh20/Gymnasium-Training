import gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.callbacks import BaseCallback
from collections import deque
import os
import bounty_handler

import torch.nn.functional as F

class CustomPolicy(nn.Module):
    def __init__(self):
        super(CustomPolicy, self).__init__()
        
        # Separate initial layers for card_info_extractor
        self.card_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Separate initial layers for betting_info_extractor
        self.betting_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Shared layers for Siamese architecture
        self.shared_layers = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(128 * 8 * 8 * 2, 512)  # Assuming input size is 64x64
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 10)
        
    def forward(self, card_info, betting_info):
        # Pass through separate initial layers
        card_features = self.card_info_extractor(card_info)
        betting_features = self.betting_info_extractor(betting_info)
        
        # Pass through shared layers
        card_features = self.shared_layers(card_features)
        betting_features = self.shared_layers(betting_features)
        
        # Flatten the features
        card_features = card_features.view(card_features.size(0), -1)
        betting_features = betting_features.view(betting_features.size(0), -1)
        
        # Concatenate the features
        combined_features = torch.cat((card_features, betting_features), dim=1)
        
        # Pass through fully connected layers
        x = F.relu(self.fc1(combined_features))
        x = F.relu(self.fc2(x))
        output = self.fc3(x)
        
        return output

class CustomPPOAgent:
    def __init__(self, env, model_path='models', n_top_models=20):
        self.env = env
        self.model_path = model_path
        self.n_top_models = n_top_models
        self.models = deque(maxlen=n_top_models)
        self.elo_ratings = []

        self.model = PPO(CustomPolicy, env, verbose=1)
        self.best_model = None

    def train(self, total_timesteps=15000, eval_freq=500):
        for i in range(0, total_timesteps, eval_freq):
            self.model.learn(total_timesteps=eval_freq)
            self.evaluate_and_store_model(i)

    def evaluate_and_store_model(self, episode):
        # Evaluate the model
        mean_reward, std_reward = self.evaluate_model()
        elo_rating = self.calculate_elo(mean_reward)

        # Store the model if it's among the top 20
        self.models.append((elo_rating, self.model))
        self.models = sorted(self.models, key=lambda x: x[0], reverse=True)[:self.n_top_models]

        # Save the model
        model_save_path = os.path.join(self.model_path, f'model_{episode}.zip')
        self.model.save(model_save_path)

    def evaluate_model(self, n_eval_episodes=10):
        rewards = []
        for _ in range(n_eval_episodes):
            obs = self.env.reset()
            done = False
            total_reward = 0
            while not done:
                action, _ = self.model.predict(obs)
                obs, reward, done, _ = self.env.step(action)
                total_reward += reward
            rewards.append(total_reward)
        mean_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        return mean_reward, std_reward

    def calculate_elo(self, mean_reward):
        # Placeholder for ELO calculation
        # You can implement a more sophisticated ELO calculation here
        return mean_reward

    def load_best_model(self):
        if self.models:
            self.best_model = self.models[0][1]

    def interact_with_environment(self, n_episodes=10):
        for _ in range(n_episodes):
            obs = self.env.reset()
            done = False
            while not done:
                action, _ = self.model.predict(obs)
                obs, reward, done, _ = self.env.step(action)
                print(f"Action: {action}, Reward: {reward}")

# Example usage
if __name__ == "__main__":
    env = gym.make('BountyHoldemEnv-v0')
    agent = CustomPPOAgent(env)
    agent.train(total_timesteps=15000)
    agent.load_best_model()
    agent.interact_with_environment(n_episodes=10)


'''
state = 

index 0: #Bet space

4x13x6
4x13 my bounty 
4x13 opponent bounty potential
4x13 hole cards
4x13 flop cards
4x13 turn cards
4x13 river cards

index 1: #Card Space

4x10x24
4 Rows: my action, opp action, sum of actions, legality of action
10 Cols: fold, check, call, bet, 1/2 pot, 3/4 pot, 1 pot, 3/2 pot, 2 pots, all in
24 Channels: Each round, 6 actions

'''