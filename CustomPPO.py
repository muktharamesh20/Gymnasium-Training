import gym
import numpy as np
import torch as th
import torch.nn.functional as F
from stable_baselines3.ppo.ppo import PPO
from stable_baselines3.common.utils import explained_variance
from stable_baselines3.common import logger

class CustomPPO(PPO):
    def __init__(self, policy, env, **kwargs):
        super(CustomPPO, self).__init__(policy, env, **kwargs)

    def train(self):
        # Update optimizer learning rate
        self._update_learning_rate(self.policy.optimizer)

        # Train for n_epochs epochs
        for epoch in range(self.n_epochs):
            approx_kl_divs = []
            for rollout_data in self.rollout_buffer.get(self.batch_size):
                actions = rollout_data.actions
                if isinstance(self.action_space, gym.spaces.Discrete):
                    # Convert discrete action from float to long
                    actions = actions.long().flatten()

                # Re-sample the noise matrix because the log_std has changed
                # See issue #417
                if self.use_sde:
                    self.policy.reset_noise(self.batch_size)

                values, log_prob, entropy = self.policy.evaluate_actions(rollout_data.observations, actions)
                values = values.flatten()

                # Normalize advantage
                advantages = rollout_data.advantages
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                # Ratio between old and new policy, should be one at the first iteration
                ratio = th.exp(log_prob - rollout_data.old_log_prob)

                # Clipped surrogate loss
                policy_loss_1 = advantages * ratio
                policy_loss_2 = advantages * th.clamp(ratio, 1 - self.clip_range, 1 + self.clip_range)
                policy_loss = -th.min(policy_loss_1, policy_loss_2).mean()

                # Value loss using the TD(gae_lambda) target
                value_loss = F.mse_loss(rollout_data.returns, values)

                # Entropy loss favor exploration
                if entropy is None:
                    # Approximate entropy when no analytical form
                    entropy_loss = -th.mean(-log_prob)
                else:
                    entropy_loss = -th.mean(entropy)

                loss = policy_loss + self.ent_coef * value_loss + self.ent_coef * entropy_loss

                # Optimization step
                self.policy.optimizer.zero_grad()
                loss.backward()
                # Clip grad norm
                th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.policy.optimizer.step()

                approx_kl_divs.append(th.mean(rollout_data.old_log_prob - log_prob).detach().cpu().numpy())

            if self.target_kl is not None and np.mean(approx_kl_divs) > 1.5 * self.target_kl:
                break

        explained_var = explained_variance(self.rollout_buffer.values.flatten(), self.rollout_buffer.returns.flatten())
        logger.record("train/explained_variance", explained_var)
        logger.record("train/learning_rate", self.lr_schedule(self._current_progress_remaining))
        logger.record("train/n_updates", self._n_updates, exclude="tensorboard")
        logger.record("train/clip_range", self.clip_range)
        if self.clip_range_vf is not None:
            logger.record("train/clip_range_vf", self.clip_range_vf)

        self._n_updates += 1