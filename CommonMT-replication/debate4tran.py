"""
MAD: Multi-Agent Debate with Large Language Models
Copyright (C) 2023  The MAD Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import json
import random
# random.seed(0)
import argparse
from langcodes import Language
from utils.agent import Agent
from datetime import datetime
from tqdm import tqdm


NAME_LIST=[
    "Affirmative side",
    "Negative side",
    "Moderator",
]

class DebatePlayer(Agent):
    def __init__(self, model_name: str, name: str, temperature:float, anthropic_api_key: str, sleep_time: float) -> None:
        """Create a player in the debate

        Args:
            model_name(str): model name
            name (str): name of this player
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            anthropic_api_key (str): As the parameter name suggests
            sleep_time (float): sleep because of rate limits
        """
        super(DebatePlayer, self).__init__(model_name, name, temperature, anthropic_api_key, sleep_time)
        self.anthropic_api_key = anthropic_api_key


class Debate:
    def __init__(self,
            model_name: str='claude-3-haiku-20240307', 
            temperature: float=0, 
            num_players: int=3, 
            save_file_dir: str=None,
            anthropic_api_key: str=None,
            prompts_path: str=None,
            max_round: int=3,
            sleep_time: float=0
        ) -> None:
        """Create a debate

        Args:
            model_name (str): openai model name
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            num_players (int): num of players
            save_file_dir (str): dir path to json file
            anthropic_api_key (str): As the parameter name suggests
            prompts_path (str): prompts path (json file)
            max_round (int): maximum Rounds of Debate
            sleep_time (float): sleep because of rate limits
        """

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.save_file_dir = save_file_dir
        self.anthropic_api_key = anthropic_api_key
        self.max_round = max_round
        self.sleep_time = sleep_time

        # init save file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        self.save_file = {
            'start_time': current_time,
            'end_time': '',
            'model_name': model_name,
            'temperature': temperature,
            'num_players': num_players,
            'success': False,
            "src_lng": "",
            "tgt_lng": "",
            'source': '',
            'reference': '',
            'base_translation': '',
            "debate_translation": '',
            "Reason": '',
            "Supported Side": '',
            'players': {},
        }
        prompts = json.load(open(prompts_path))
        self.save_file.update(prompts)
        self.init_prompt()

        if self.save_file['base_translation'] == "":
            self.create_base()

        # creat&init agents
        self.creat_agents()
        self.init_agents()


    def init_prompt(self):
        def prompt_replace(key):
            self.save_file[key] = self.save_file[key].replace("##src_lng##", self.save_file["src_lng"]).replace("##tgt_lng##", self.save_file["tgt_lng"]).replace("##source##", self.save_file["source"]).replace("##base_translation##", self.save_file["base_translation"])
        prompt_replace("base_prompt")
        prompt_replace("player_meta_prompt")
        prompt_replace("moderator_meta_prompt")
        prompt_replace("judge_prompt_last2")

    def create_base(self):
        print(f"\n===== Translation Task =====\n{self.save_file['base_prompt']}\n")
        agent = DebatePlayer(model_name=self.model_name, name='Baseline', temperature=self.temperature, anthropic_api_key=self.anthropic_api_key, sleep_time=self.sleep_time)
        agent.add_event(self.save_file['base_prompt'])
        base_translation = agent.ask()
        agent.add_memory(base_translation)
        self.save_file['base_translation'] = base_translation
        self.save_file['affirmative_prompt'] = self.save_file['affirmative_prompt'].replace("##base_translation##", base_translation)
        self.save_file['players'][agent.name] = agent.memory_lst

    def creat_agents(self):
        # creates players
        self.players = [
            DebatePlayer(model_name=self.model_name, name=name, temperature=self.temperature, anthropic_api_key=self.anthropic_api_key, sleep_time=self.sleep_time) for name in NAME_LIST
        ]
        self.affirmative = self.players[0]
        self.negative = self.players[1]
        self.moderator = self.players[2]

    def init_agents(self):
        # start: set meta prompt
        self.affirmative.set_meta_prompt(self.save_file['player_meta_prompt'])
        self.negative.set_meta_prompt(self.save_file['player_meta_prompt'])
        self.moderator.set_meta_prompt(self.save_file['moderator_meta_prompt'])
        
        # start: first round debate, state opinions
        print(f"===== Debate Round-1 =====\n")
        self.affirmative.add_event(self.save_file['affirmative_prompt'])
        self.aff_ans = self.affirmative.ask()
        self.affirmative.add_memory(self.aff_ans)

        self.negative.add_event(self.save_file['negative_prompt'].replace('##aff_ans##', self.aff_ans))
        self.neg_ans = self.negative.ask()
        self.negative.add_memory(self.neg_ans)

        self.moderator.add_event(self.save_file['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', 'first'))
        self.mod_ans = self.moderator.ask()
        self.moderator.add_memory(self.mod_ans)
        self.mod_ans = json.loads(self.mod_ans)

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }
        return dct[num]
            
    def save_file_to_json(self, id):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        save_file_path = os.path.join(self.save_file_dir, f"{id}.json")
        
        self.save_file['end_time'] = current_time
        json_str = json.dumps(self.save_file, ensure_ascii=False, indent=4)
        with open(save_file_path, 'w') as f:
            f.write(json_str)

    def broadcast(self, msg: str):
        """Broadcast a message to all players. 
        Typical use is for the host to announce public information

        Args:
            msg (str): the message
        """
        # print(msg)
        for player in self.players:
            player.add_event(msg)

    def speak(self, speaker: str, msg: str):
        """The speaker broadcast a message to all other players. 

        Args:
            speaker (str): name of the speaker
            msg (str): the message
        """
        if not msg.startswith(f"{speaker}: "):
            msg = f"{speaker}: {msg}"
        # print(msg)
        for player in self.players:
            if player.name != speaker:
                player.add_event(msg)

    def ask_and_speak(self, player: DebatePlayer):
        ans = player.ask()
        player.add_memory(ans)
        self.speak(player.name, ans)


    def run(self):

        for round in range(self.max_round - 1):

            if self.mod_ans["debate_translation"] != '':
                break
            else:
                print(f"===== Debate Round-{round+2} =====\n")
                self.affirmative.add_event(self.save_file['debate_prompt'].replace('##oppo_ans##', self.neg_ans))
                self.aff_ans = self.affirmative.ask()
                self.affirmative.add_memory(self.aff_ans)

                self.negative.add_event(self.save_file['debate_prompt'].replace('##oppo_ans##', self.aff_ans))
                self.neg_ans = self.negative.ask()
                self.negative.add_memory(self.neg_ans)

                self.moderator.add_event(self.save_file['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', self.round_dct(round+2)))
                self.mod_ans = self.moderator.ask()
                self.moderator.add_memory(self.mod_ans)
                self.mod_ans = json.loads(self.mod_ans)

        if self.mod_ans["debate_translation"] != '':
            self.save_file.update(self.mod_ans)
            self.save_file['success'] = True

        # ultimate deadly technique.
        else:
            judge_player = DebatePlayer(model_name=self.model_name, name='Judge', temperature=self.temperature, anthropic_api_key=self.anthropic_api_key, sleep_time=self.sleep_time)
            aff_ans = self.affirmative.memory_lst[2]['content']
            neg_ans = self.negative.memory_lst[2]['content']

            judge_player.set_meta_prompt(self.save_file['moderator_meta_prompt'])

            # extract answer candidates
            judge_player.add_event(self.save_file['judge_prompt_last1'].replace('##aff_ans##', aff_ans).replace('##neg_ans##', neg_ans))
            ans = judge_player.ask()
            judge_player.add_memory(ans)

            # select one from the candidates
            judge_player.add_event(self.save_file['judge_prompt_last2'])
            ans = judge_player.ask()
            judge_player.add_memory(ans)
            
            ans = json.loads(ans)
            if ans["debate_translation"] != '':
                self.save_file['success'] = True
                # save file
            self.save_file.update(ans)
            self.players.append(judge_player)

        for player in self.players:
            self.save_file['players'][player.name] = player.memory_lst


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str, required=True, help="Input file path")
    parser.add_argument("-o", "--output-dir", type=str, required=True, help="Output file dir")
    parser.add_argument("-lp", "--lang-pair", type=str, required=True, help="Language pair")
    parser.add_argument("-k", "--api-key", type=str, required=True, help="Anthropic api key")
    parser.add_argument("-m", "--model-name", type=str, default="claude-3-haiku-20240307", help="Model name")
    parser.add_argument("-t", "--temperature", type=float, default=0, help="Sampling temperature")

    return parser.parse_args()


def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)


def load_api_key(api_key_path='api_key.txt'):
    """Load API key from file"""
    if not os.path.exists(api_key_path):
        raise FileNotFoundError(f"API key file not found: {api_key_path}")
    
    with open(api_key_path, 'r') as f:
        api_key = f.read().strip()
    
    if not api_key:
        raise ValueError("API key file is empty")
    
    return api_key


if __name__ == "__main__":
    # Load configuration from file
    config = load_config('config4tran.json')
    
    # Load API key from separate file
    anthropic_api_key = load_api_key('api-key.txt')
    
    # Extract configuration values
    input_file = config.get('input_file', 'hindi-english-input.txt')
    output_dir = config.get('output_dir', './hindi-english-output-claude-sonnet-4-5-20250929')
    lang_pair = config.get('lang_pair', 'hi-en')
    model_name = config.get('model_name', 'claude-sonnet-4-5-20250929')
    temperature = config.get('temperature', 0)  #temp set to 0 or all rounds
    max_round = config.get('max_round', 3)
    sleep_time = config.get('sleep_time', 0)
    
    # # Get the path to config4tran.json
    current_script_path = os.path.abspath(__file__)
    MAD_path = current_script_path.rsplit("/", 2)[0]
    config4tran_path = f"{MAD_path}/code/utils/config4tran.json"
    
    # Parse language pair
    src_lng, tgt_lng = lang_pair.split('-')
    src_full = Language.make(language=src_lng).display_name()
    tgt_full = Language.make(language=tgt_lng).display_name()
    
    # Load debate prompts template
    debate_config = json.load(open(config4tran_path, "r"))
    
    # Read input file
    inputs = open(input_file, "r").readlines()
    inputs = [l.strip() for l in inputs]
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Processing {len(inputs)} translations...")
    print(f"Language pair: {src_full} → {tgt_full}")
    print(f"Model: {model_name}")
    print(f"Output directory: {output_dir}\n")
    
    # Process each input line
    for id, input_line in enumerate(tqdm(inputs)):
        # Skip if already processed (optional)
        if os.path.exists(f"{output_dir}/{id}.json"):
            continue
        
        # Split source and reference
        parts = input_line.split('\t')
        if len(parts) != 2:
            print(f"Warning: Line {id} doesn't have proper format (source\\treference). Skipping.")
            continue
        
        # Create config for this specific translation
        prompts_path = f"config-files/{id}-config.json"
        
        debate_config['source'] = parts[0]
        debate_config['reference'] = parts[1]
        debate_config['src_lng'] = src_full
        debate_config['tgt_lng'] = tgt_full
        
        with open(prompts_path, 'w') as file:
            json.dump(debate_config, file, ensure_ascii=False, indent=4)
        
        # Run the debate
        debate = Debate(
            save_file_dir=output_dir,
            num_players=3,
            anthropic_api_key=anthropic_api_key,
            prompts_path=prompts_path,
            temperature=temperature,
            sleep_time=sleep_time,
            model_name=model_name,
            max_round=max_round
        )
        debate.run()
        debate.save_file_to_json(id)
    
    print(f"\nProcessing complete! Results saved to {output_dir}/")

