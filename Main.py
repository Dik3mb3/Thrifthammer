#Roster Selection 
import Sideline_Staff
import sys
import Skaven_Roster, Wood_Elf_Roster, Amazon_Roster, Chaos_Chosen_Roster, Underworld_Roster,Black_Orcs_Roster, Dark_Elves_Roster, High_Elf_Roster, Lizardman_Roster, Necro_Roster, Nurgle_Roster, Orc_Roster, Goblins_Roster, Undead_Roster, Vampire_Roster, Tomb_Kings_Roster, Norse_Roster, Ogre_Roster, Dwarves_Roster, Human_Roster, Halfling_Roster, Nobs_Roster, Slann_Roster, Snotling_Roster, OWA_Roster, Gnome_Roster, Chaos_Dwarves_Roster, Elven_Union_Roster

choice = ''

roster_cost = 0 

def main_menu():
    global choice
    print("Roster Selection Menu")
    print("1. Skaven Roster")
    print("2. Wood Elf Roster")
    print('3. Amazon Roster')
    print("4. Chaos Roster")
    print("5. Underworld Roster")
    print("6. Black Orcs Roster")
    print("7. Dark Elves Roster")
    print("8. High Elves Roster")
    print("9. Lizardmen Roster")
    print("10. Necromantic Roster")
    print("11. Nurgle Roster")
    print("12. Orc Roster")
    print("13. Goblins Roster")
    print("14. Undead Roster")
    print("15. Vampire Roster")
    print("16. Tomb Kings Roster")
    print("17. Norse Roster")
    print("18. Ogre Roster")
    print("19. Dwarves Roster")
    print("20. Human Roster")
    print("21. Halfling Roster")
    print("22. Nobs Roster")
    print("23. Slann Roster")
    print("24. Snotling Roster")
    print("25. Old World Alliance Roster")
    print("26. Gnome Roster")
    print("27. Chaos Dwarves Roster")
    print("28. Elven Union Roster")
    print("29. Exit")
    print('------------------------------------------------------------------------')
    choice = input("Select a roster (1-29): ")
    if choice == '29':
        sys.exit()
    else:
        return choice
    

def load_roster(choice):
    rosters = {
        '1': Skaven_Roster,
        '2': Wood_Elf_Roster,
        '3': Amazon_Roster,
        '4': Chaos_Chosen_Roster,
        '5': Underworld_Roster,
        '6': Black_Orcs_Roster,
        '7': Dark_Elves_Roster,
        '8': High_Elf_Roster,
        '9': Lizardman_Roster,
        '10': Necro_Roster,
        '11': Nurgle_Roster,
        '12': Orc_Roster,
        '13': Goblins_Roster,
        '14': Undead_Roster,
        '15': Vampire_Roster,
        '16': Tomb_Kings_Roster,
        '17': Norse_Roster,
        '18': Ogre_Roster,
        '19': Dwarves_Roster,
        '20': Human_Roster,
        '21': Halfling_Roster,
        '22': Nobs_Roster,
        '23': Slann_Roster,
        '24': Snotling_Roster,
        '25': OWA_Roster,
        '26': Gnome_Roster,
        '27': Chaos_Dwarves_Roster,
        '28': Elven_Union_Roster
    }
    return rosters.get(choice, None)

def display_roster(roster):
    if roster is None:
        print("Invalid selection.")
        return
    print("Roster Details:")
    print(f"Team: {roster.roster_name}")
    print(f"Rerolls: {roster.rerolls}")
    print(f"Apothecary: {roster.Apothecary}")
    print(f"Tier: {roster.Tier}")
    print(f"Leagues: {roster.Leagues}")

    for pos in roster.Name:
        print('----------------------------------------')
        print(f"Position: {pos}")
        print(f"  Name: {roster.Name[pos]}")
        print(f"  Cost: {roster.Cost[pos]}")
        print(f"  Quantity: {roster.Quantity[pos]}")
        stats = roster.Stats[pos]
        print(f"  Stats: MA={stats['MA']}, ST={stats['ST']}, AG={stats['AG']}, PA={stats['PA']}, AV={stats['AV']}")
        skills = roster.Skills.get(pos, [])
        print(f"  Skills: {', '.join(skills) if skills else 'None'}")
        print()
    print('-------------------------------------------------------------------------------')
    print('Do you want to build a roster, choosing n will return you to main_menu? (y/n)')
    response = input().lower()
    if response == 'y':
        build_roster(roster)
    else:
        main_menu()

def build_roster(roster): 
   with open('Custom_Roster.txt', 'w') as f:
        sideline_staff(roster)
        roster_count(roster)
    

def sideline_staff (roster): 
    global roster_cost
    with open('Custom_Roster.txt', 'a') as f:
        if roster.Apothecary == True:
            print(f'Do you want to add an Apothecary for {Sideline_Staff.Apothecary}? (y/n)')
            response = input().lower()
            if response == 'y':
                f.write(f'Apothecary: {Sideline_Staff.Apothecary}\n')
                roster_cost += Sideline_Staff.Apothecary
        print(f'How many coaches for {Sideline_Staff.Coaches}?')
        coaches = int(input())
        if coaches > 0 and coaches <= Sideline_Staff.max_count['Coaches']:
            f.write(f'Coaches: {coaches} x {Sideline_Staff.Coaches} = {coaches * Sideline_Staff.Coaches}\n')
            roster_cost += coaches * Sideline_Staff.Coaches
        else: 
            print('Invalid number of coaches. No coaches added.')
        print(f'How many cheerleaders for {Sideline_Staff.Cheerleaders}?')
        cheerleaders = int(input())
        if cheerleaders > 0 and cheerleaders <= Sideline_Staff.max_count['Cheerleaders']:
            f.write(f'Cheerleaders: {cheerleaders} x {Sideline_Staff.Cheerleaders} = {cheerleaders * Sideline_Staff.Cheerleaders}\n')
            roster_cost += cheerleaders * Sideline_Staff.Cheerleaders
        else: 
            print('Invalid number of cheerleaders. No cheerleaders added.')

def roster_count(roster):
    global roster_cost
    with open('Custom_Roster.txt', 'a') as f:
        for pos in roster.Name:
            count = int(input(f'How many {roster.Name[pos]} would you like to add? (Max {roster.Quantity[pos]}): '))
            if count <= roster.Quantity[pos]:
                f.write(f'{pos}: {count}\n')
                roster_cost += int(count) * roster.Cost[pos]
            else:
                print('Exceeds maximum quantity. Adding maximum allowed.')
                roster_cost += int(count) * roster.Cost[pos]
    print(f'Current Roster Cost: {roster_cost}')

    
        

main_menu()
load_roster(choice)
display_roster(load_roster(choice))
