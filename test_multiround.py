"""
Test script to verify multi-round debate functionality
Run this to check if your debate system properly handles multiple rounds
"""

import os
import json
import sys

# Add parent directory to path to import the debate module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your debate class
from interactive import Debate

# Your API key
anthropic_api_key = "<Enter API key>"

def test_multi_round_debate():
    """Test that debates can go multiple rounds"""
    
    print("=" * 70)
    print("MULTI-ROUND DEBATE TEST")
    print("=" * 70)
    print("\nThis test will verify if your debate system properly handles")
    print("multiple rounds of debate before reaching a conclusion.\n")
    
    # Test topics that should generate good debate
    test_topics = [
        "Is artificial intelligence more beneficial than harmful to society?",
        "Should remote work become the permanent standard for office jobs?",
        "Is social media doing more harm than good?"
    ]
    
    print("Select a test topic:")
    for i, topic in enumerate(test_topics, 1):
        print(f"  {i}. {topic}")
    
    choice = input("\nEnter number (or press Enter for topic 1): ").strip()
    topic_idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= 3 else 0
    
    debate_topic = test_topics[topic_idx]
    
    # Load the multi-round config
    config_path = "config4all_multiround.json"
    if not os.path.exists(config_path):
        print(f"\n❌ Error: {config_path} not found!")
        print("Please ensure config4all_multiround.json is in the same directory.")
        return
    
    config = json.load(open(config_path, "r"))
    config['debate_topic'] = debate_topic
    
    print(f"\n{'='*70}")
    print(f"Testing with topic: {debate_topic}")
    print(f"Maximum rounds allowed: 3")
    print(f"{'='*70}\n")
    
    # Track rounds
    rounds_completed = []
    
    # Monkey-patch to track rounds
    original_init_agents = Debate.init_agents
    original_run = Debate.run
    
    def tracked_init_agents(self):
        print("\n🔵 TRACKING: Round 1 starting...")
        original_init_agents(self)
        rounds_completed.append(1)
        print(f"✅ TRACKING: Round 1 completed. Moderator decision: debate_answer='{self.mod_ans.get('debate_answer', 'EMPTY')}'")
    
    def tracked_run(self):
        original_run(self)
        # Count how many rounds actually happened
        total_rounds = len([p for p in self.players if p.name in ["Affirmative side", "Negative side", "Moderator"]])
        
    Debate.init_agents = tracked_init_agents
    
    try:
        debate = Debate(
            model_name='claude-sonnet-4-5-20250929',
            num_players=3,
            anthropic_api_key=anthropic_api_key,
            config=config,
            temperature=0,
            sleep_time=0,
            max_round=3  # Allow up to 3 rounds
        )
        
        # Override run to track rounds
        print("\n🟢 Starting debate with round tracking...\n")
        
        for round_num in range(debate.max_round - 1):
            if debate.mod_ans.get("debate_answer", "") != '':
                print(f"\n🏁 TRACKING: Debate concluded after checking round {round_num + 1}")
                break
            else:
                current_round = round_num + 2
                print(f"\n🔵 TRACKING: Round {current_round} starting...")
                rounds_completed.append(current_round)
                
                debate.affirmative.add_event(debate.config['debate_prompt'].replace('##oppo_ans##', debate.neg_ans))
                debate.aff_ans = debate.affirmative.ask()
                debate.affirmative.add_memory(debate.aff_ans)

                debate.negative.add_event(debate.config['debate_prompt'].replace('##oppo_ans##', debate.aff_ans))
                debate.neg_ans = debate.negative.ask()
                debate.negative.add_memory(debate.neg_ans)

                debate.moderator.add_event(debate.config['moderator_prompt'].replace('##aff_ans##', debate.aff_ans).replace('##neg_ans##', debate.neg_ans).replace('##round##', debate.round_dct(current_round)))
                debate.mod_ans = debate.moderator.ask()
                debate.moderator.add_memory(debate.mod_ans)
                debate.mod_ans = debate.safe_parse_json(debate.mod_ans, f"moderator round {current_round}")
                
                print(f"✅ TRACKING: Round {current_round} completed. Moderator decision: debate_answer='{debate.mod_ans.get('debate_answer', 'EMPTY')}'")

        if debate.mod_ans.get("debate_answer", "") != '':
            debate.config.update(debate.mod_ans)
            debate.config['success'] = True
        else:
            print(f"\n⚠️  TRACKING: Reached max rounds without conclusion. Activating judge...")
        
        debate.print_answer()
        
        # Analysis
        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(f"\n✅ Total rounds completed: {len(rounds_completed)}")
        print(f"   Rounds: {rounds_completed}")
        
        if len(rounds_completed) == 1:
            print("\n⚠️  WARNING: Only 1 round occurred!")
            print("   This means the moderator concluded too early.")
            print("   Check your moderator_prompt to ensure it requires multiple rounds.")
        elif len(rounds_completed) >= 2:
            print(f"\n✅ SUCCESS: Multiple rounds occurred ({len(rounds_completed)} rounds)")
            print("   Your debate system properly handles multi-round debates!")
        
        print(f"\nFinal decision: {debate.config.get('debate_answer', 'None')}")
        print(f"Reasoning: {debate.config.get('Reason', 'None')[:100]}...")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore original methods
        Debate.init_agents = original_init_agents
        Debate.run = original_run


def analyze_current_config():
    """Analyze your current config to see why debates might end early"""
    
    print("\n" + "=" * 70)
    print("CONFIG ANALYSIS")
    print("=" * 70)
    
    config_paths = [
        "code/utils/config4all.json",
        "../code/utils/config4all.json",
        "config4all.json"
    ]
    
    config = None
    config_path = None
    
    for path in config_paths:
        if os.path.exists(path):
            config_path = path
            config = json.load(open(path, "r"))
            break
    
    if not config:
        print("\n❌ Could not find config4all.json in expected locations:")
        for path in config_paths:
            print(f"   - {path}")
        return
    
    print(f"\n✅ Found config at: {config_path}\n")
    
    # Check moderator prompt
    mod_prompt = config.get('moderator_meta_prompt', '')
    
    print("🔍 Analyzing moderator_meta_prompt:")
    print("-" * 70)
    
    issues = []
    suggestions = []
    
    if "debate_answer" not in mod_prompt.lower():
        issues.append("❌ Doesn't mention 'debate_answer' field")
        suggestions.append("Add instructions about when to fill debate_answer")
    else:
        print("✅ Mentions 'debate_answer' field")
    
    if "empty" not in mod_prompt.lower() and '""' not in mod_prompt:
        issues.append("⚠️  Doesn't explicitly mention empty debate_answer for early rounds")
        suggestions.append("Add: 'Return {\"debate_answer\": \"\"} for rounds 1-2'")
    else:
        print("✅ Mentions empty debate_answer")
    
    if "first" not in mod_prompt.lower() and "round" not in mod_prompt.lower():
        issues.append("⚠️  Doesn't distinguish between rounds")
        suggestions.append("Add round-specific instructions")
    else:
        print("✅ Has round-specific logic")
    
    if "json" not in mod_prompt.lower():
        issues.append("⚠️  Doesn't emphasize JSON format")
        suggestions.append("Add: 'Respond with ONLY valid JSON'")
    else:
        print("✅ Emphasizes JSON format")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"   {issue}")
        
        print(f"\n💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
        
        print("\n📝 Consider using the config4all_multiround.json template!")
    else:
        print("\n✅ Config looks good for multi-round debates!")
    
    print("\nCurrent moderator_meta_prompt:")
    print("-" * 70)
    print(mod_prompt[:500] + "..." if len(mod_prompt) > 500 else mod_prompt)


if __name__ == "__main__":
    print("\nMulti-Round Debate Test Suite")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Run multi-round debate test")
    print("  2. Analyze current config file")
    print("  3. Both")
    
    choice = input("\nSelect option (1-3, default=3): ").strip() or "3"
    
    if choice in ["2", "3"]:
        analyze_current_config()
    
    if choice in ["1", "3"]:
        print("\n")
        test_multi_round_debate()
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)