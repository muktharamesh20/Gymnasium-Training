import torch as th
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.distributions import make_proba_distribution

class CustomPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super(CustomPolicy, self).__init__(*args, **kwargs)
        
        # Separate initial layers for card_info_extractor
        self.card_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=4, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # Separate initial layers for betting_info_extractor
        self.betting_info_extractor = nn.Sequential(
            nn.Conv2d(in_channels=4, out_channels=32, kernel_size=3, stride=1, padding=1),
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
        self.action_net = nn.Linear(256, self.action_space.n)
        self.value_net = nn.Linear(256, 1)

    def forward(self, obs, deterministic=False):
        card_info, betting_info = obs
        card_info = self.card_info_extractor(card_info)
        betting_info = self.betting_info_extractor(betting_info)
        
        card_info = self.shared_layers(card_info)
        betting_info = self.shared_layers(betting_info)
        
        card_info = card_info.view(card_info.size(0), -1)
        betting_info = betting_info.view(betting_info.size(0), -1)
        
        combined = th.cat((card_info, betting_info), dim=1)
        
        x = F.relu(self.fc1(combined))
        x = F.relu(self.fc2(x))
        
        action_logits = self.action_net(x)
        value = self.value_net(x)
        
        return action_logits, value

    def _build(self, lr_schedule):
        super(CustomPolicy, self)._build(lr_schedule)
        
        # Modify the loss function here
        self.loss_fn = nn.MSELoss()

    def evaluate_actions(self, obs, actions):
        action_logits, value = self.forward(obs)
        distribution = self._get_action_dist_from_latent(action_logits)
        log_prob = distribution.log_prob(actions)
        entropy = distribution.entropy()
        return value, log_prob, entropy

    def custom_loss(self, values, log_prob, entropy, rewards, old_log_prob, advantages, clip_range, clip_range_vf, delta1, delta2, delta3):
        # Implement the Trinal-Clip PPO loss function here
        ratio = th.exp(log_prob - old_log_prob)
        surr1 = ratio * advantages
        surr2 = th.clamp(ratio, 1 - clip_range, 1 + clip_range) * advantages
        surr3 = th.clamp(ratio, 1 - clip_range, delta1) * advantages
        policy_loss = -th.mean(th.min(surr1, th.min(surr2, surr3)))

        clipped_value = values + th.clamp(rewards - values, -delta2, delta3)
        value_loss = self.loss_fn(clipped_value, rewards)
        
        entropy_loss = -th.mean(entropy)
        
        loss = policy_loss + value_loss + entropy_loss
        return loss