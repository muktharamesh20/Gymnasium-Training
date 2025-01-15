# FILE: siamese_policy.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import MlpExtractor

class SiameseNetwork(nn.Module):
    def __init__(self, input_shape):
        super(SiameseNetwork, self).__init__()
        
        # Separate initial layers for card_info_extractor
        self.card_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=4, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        
        # Separate initial layers for betting_info_extractor
        self.betting_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=4, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        
        # Shared layers for Siamese architecture
        self.shared_layers = nn.Sequential(
            nn.Conv2d(in_channels=16, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(768,100)  # Assuming input size is 64x64
        self.fc2 = nn.Linear(100, 256)
        self.action_net = nn.Linear(256, 9)
        self.value_net = nn.Linear(256, 1)

    def forward(self, x):
        x = x.to(torch.float32)

        print(f"Shape of x: {x.shape}")

        card_info = x[:,:,:,:6]
        betting_info = x[:,:,:,6:]

        print(f"Shape of card_info: {card_info.shape}")
        print(f"Shape of betting_info: {betting_info.shape}")

        card_features = self.card_info_extractor(card_info)
        betting_features = self.betting_info_extractor(betting_info)

        print(f"Shape of card_features: {card_features.shape}")
        print(f"Shape of betting_features: {betting_features.shape}")
        
        combined_features = torch.cat((card_features, betting_features), dim=3)

        print(f"Shape of combined_features: {combined_features.shape}")
        shared_features = self.shared_layers(combined_features)
        print(f"Shape of shared_features: {shared_features.shape}")
        shared_features = shared_features.view(shared_features.size(0), -1)

        x = F.relu(self.fc1(shared_features))
        x = F.relu(self.fc2(x))
        print(f'Shape of x: {x.shape}')
        return x

class SiamesePolicy(ActorCriticPolicy):
    def __init__(self, observation_space, action_space, lr_schedule, *args, **kwargs):
        super(SiamesePolicy, self).__init__(observation_space, action_space, lr_schedule, *args, **kwargs)
        self.siamese_net = SiameseNetwork(observation_space.shape)
        # Example input dimensions
        input_dim = 256
        net_arch = [128, 256]  # Two hidden layers with 128 and 64 units

        # Create an MLPExtractor
        mlp_extractor = MlpExtractor(
            feature_dim=input_dim,
            net_arch=net_arch,
            activation_fn=torch.nn.ReLU
        )
        self.mlp_extractor = mlp_extractor
        self.action_space = action_space
        self.action_net = nn.Linear(256, 9)
        self.value_net = nn.Linear(256, 1)

    def forward(self, obs, deterministic=False):
        features = self.siamese_net(obs)
        latent_pi, latent_vf = self.mlp_extractor(features)
        distribution = self._get_action_dist_from_latent(latent_pi)
        actions = distribution.get_actions(deterministic=deterministic)
        values = self.value_net(latent_vf)
        print("here", self.value_net)
        return actions, values, distribution.log_prob(actions)

    def _predict(self, observation, deterministic=False):
        actions, _, _ = self.forward(observation, deterministic=deterministic)
        return actions

    def evaluate_actions(self, obs, actions):
        card_info, betting_info = obs[:, :4, :, :], obs[:, 4:, :, :]
        features = self.siamese_net(card_info, betting_info)
        latent_pi, latent_vf = self.mlp_extractor(features)
        distribution = self._get_action_dist_from_latent(latent_pi)
        log_prob = distribution.log_prob(actions)
        entropy = distribution.entropy()
        values = self.value_net(latent_vf)
        return values, log_prob, entropy