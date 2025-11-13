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
import re
# random.seed(0)
from code.utils.agent import Agent


anthropic_api_key = "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"

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
            anthropic_api_key: str=None,
            config: dict=None,
            max_round: int=3,
            sleep_time: float=0
        ) -> None:
        """Create a debate

        Args:
            model_name (str): openai model name
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            num_players (int): num of players
            anthropic_api_key (str): As the parameter name suggests
            config (dict): Configuration dictionary with prompts
            max_round (int): maximum Rounds of Debate
            sleep_time (float): sleep because of rate limits
        """

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.anthropic_api_key = anthropic_api_key
        self.config = config
        self.max_round = max_round
        self.sleep_time = sleep_time

        self.init_prompt()
        print(f"model selected = {self.model_name}")
        # creat&init agents
        self.creat_agents()
        self.init_agents()


    def init_prompt(self):
        def prompt_replace(key):
            self.config[key] = self.config[key].replace("##debate_topic##", self.config["debate_topic"])
        prompt_replace("player_meta_prompt")
        prompt_replace("moderator_meta_prompt")
        prompt_replace("affirmative_prompt")
        prompt_replace("judge_prompt_last2")

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
        self.affirmative.set_meta_prompt(self.config['player_meta_prompt'])
        self.negative.set_meta_prompt(self.config['player_meta_prompt'])
        self.moderator.set_meta_prompt(self.config['moderator_meta_prompt'])
        
        # start: first round debate, state opinions
        print(f"===== Debate Round-1 =====\n")
        self.affirmative.add_event(self.config['affirmative_prompt'])
        self.aff_ans = self.affirmative.ask()
        self.affirmative.add_memory(self.aff_ans)
        self.config['base_answer'] = self.aff_ans

        print("af---------------------")

        self.negative.add_event(self.config['negative_prompt'].replace('##aff_ans##', self.aff_ans))
        self.neg_ans = self.negative.ask()
        self.negative.add_memory(self.neg_ans)

        print("n---------------------")

        self.moderator.add_event(self.config['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', 'first'))
        self.mod_ans = self.moderator.ask()
        # print("AFTER ASK")
        # print(self.mod_ans)
        # print("---------------------")
        print("1---------------------")
        self.moderator.add_memory(self.mod_ans)
        #self.mod_ans = eval(self.mod_ans)
        print("2_____________")
        self.mod_ans = self.safe_parse_json(self.mod_ans, "moderator round 1")
        print("3---------------------")
        print(self.mod_ans)

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }
        return dct[num]
    
    def safe_parse_json(self, response:str, context:str = ""):
        """ parse response
        Args:
            response(str): The response string to parse
            context(str): Context for error messages

        Returns:
            dict: parsed dictionary or default structure
        """
        cleaned = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        cleaned = re.sub(r'```\s*\n?', '', cleaned)
        cleaned = cleaned.strip()

        json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
        json_matches = re.findall(json_pattern, cleaned, re.DOTALL)

        if json_matches:
            for json_str in json_matches:
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError as e:
                    continue

        try:
            result = json.loads(cleaned)
            return result
        except json.JSONDecodeError:
            pass
        
        print(f"could not parse {context}")
        print(context)

        return{
            "debate_answer":"",
            "Reason": f"failed to parse response from {context}",
            "Supported Side":""
        }


    def print_answer(self):
        print("\n\n===== Debate Done! =====")
        print("\n----- Debate Topic -----")
        print(self.config.get("debate_topic", "N/A"))
        print("\n----- Base Answer -----")
        print(self.config.get("base_answer", "N/A"))
        print("\n----- Debate Answer -----")
        print(self.config.get("debate_answer", "N/A"))
        print("\n----- Debate Reason -----")
        print(self.config.get("Reason", "N/A"))

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
        print("entered ru function")

        for round in range(self.max_round - 1):
            print("entered for loop")
            print(self.mod_ans["debate_answer"])

            if self.mod_ans["debate_answer"] != '': #self.mod_ans.get("debate_answer", "") != ''  --or-- false
                print("entered if")
                break
            else:
                print(f"===== Debate Round-{round+2} =====\n")
                self.affirmative.add_event(self.config['debate_prompt'].replace('##oppo_ans##', self.neg_ans))
                self.aff_ans = self.affirmative.ask()
                self.affirmative.add_memory(self.aff_ans)

                self.negative.add_event(self.config['debate_prompt'].replace('##oppo_ans##', self.aff_ans))
                self.neg_ans = self.negative.ask()
                self.negative.add_memory(self.neg_ans)

                self.moderator.add_event(self.config['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', self.round_dct(round+2)))
                self.mod_ans = self.moderator.ask()
                self.moderator.add_memory(self.mod_ans)
                self.mod_ans = self.safe_parse_json(self.mod_ans, f"moderator round {round + 2}")
                print("finished path")
                # self.mod_ans = eval(self.mod_ans)


        if self.mod_ans["debate_answer"] != '':
            print("entered if")
            self.config.update(self.mod_ans)
            self.config['success'] = True

        # ultimate deadly technique.
        else:
            print("entered else")
            judge_player = DebatePlayer(model_name=self.model_name, name='Judge', temperature=self.temperature, anthropic_api_key=self.anthropic_api_key, sleep_time=self.sleep_time)
            aff_ans = self.affirmative.memory_lst[2]['content']
            neg_ans = self.negative.memory_lst[2]['content']

            judge_player.set_meta_prompt(self.config['moderator_meta_prompt'])

            # extract answer candidates
            judge_player.add_event(self.config['judge_prompt_last1'].replace('##aff_ans##', aff_ans).replace('##neg_ans##', neg_ans))
            ans = judge_player.ask()
            judge_player.add_memory(ans)

            # select one from the candidates
            judge_player.add_event(self.config['judge_prompt_last2'])
            ans = judge_player.ask()
            judge_player.add_memory(ans)
            
            ans = self.safe_parse_json(ans, "judge final decision")
            if ans.get("debate_answer","") != '':
                self.config['success'] = True
                # save file
            self.config.update(ans)
            self.players.append(judge_player)

        self.print_answer()


if __name__ == "__main__":

    current_script_path = os.path.abspath(__file__)
    MAD_path = current_script_path.rsplit("/", 1)[0]

    print("=" * 60)
    print("Claude-Powered Multi-Agent Debate System")
    print("=" * 60)
    print("\nAvailable Claude Models:")
    print("claude-sonnet-4-5-20250929")
    print("claude-3-5-sonnet-20241022")
    print("claude-3-opus-20240229")
    print("claude-3-sonnet-20240229")
    print("claude-3-haiku-20240307 (fastest)")
    print("\nType 'quit' or 'exit' to end program.\n")

    while True:
        debate_topic = ""
        while debate_topic == "":
            debate_topic = input(f"\nEnter your debate topic (or 'quit' to exit): ").strip()
            
            if debate_topic.lower()in ['quit', 'exit', 'q']:
                print("\n Thanks for using the MAD system")
                exit(0)
            
            if debate_topic == "":
                print("Please enter a valid debate topic")

        try:
            config = json.load(open(f"{MAD_path}/code/utils/config4all.json", "r"))
            config['debate_topic'] = debate_topic

            debate = Debate(model_name='claude-3-haiku-20240307',num_players=3, anthropic_api_key=anthropic_api_key, config=config, temperature=0.7, sleep_time=0)
            print("about to enter run")
            debate.run()
            print("finished run")

        except FileNotFoundError as e:
            print(f"\n❌ Config file not found: {e}")
            print("Please ensure config4all.json exists at code/utils/config4all.json")
            continue

        except KeyError as e:
            print(f"\n❌ Missing key in config: {e}")
            print("Please check your config file has all required prompts")
            continue

        except Exception as e:
            print(f"Error occured - {e}")
            continue

