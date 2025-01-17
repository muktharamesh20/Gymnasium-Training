# FILE: agent.py

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from ProbabilityStatesEnv import BountyHoldemEnv
from siamese_policy import SiamesePolicy
import gymnasium as gym


def mask_fn(env: gym.Env):
    return env.get_legal_action_mask()

env = BountyHoldemEnv()
env = ActionMasker(env, mask_fn)

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