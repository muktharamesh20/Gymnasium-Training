import gym
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from Environment import BountyHoldemEnv
import numpy
import time

env = BountyHoldemEnv()
env.reset()

models_dir = "models/masked_nenv-ent1-10k"
model_path = f"{models_dir}/1490000" 

def mask_fn(env: gym.Env):
    return env.get_legal_action_mask()

env = BountyHoldemEnv()
env = ActionMasker(env, mask_fn)

model = MaskablePPO.load(model_path, env=env)

episodes = 100

for ep in range(episodes):
    obs, _ = env.reset()
    done = False
    while not done:
        #env.render()
        action, _ = model.predict(obs, action_masks=obs[3, :9, 6])
        valid_actions = []

        for index, i in enumerate(obs[3, :9, 6]):
            if i == 1:
                valid_actions.append(index)
        #env.render()
        #print("Valid Actions", valid_actions)
        #print("Chosen Action", action)
        obs, reward, done, trunc, info = env.step(action)
        #time.sleep(5)


env.close()