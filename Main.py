#Roster Selection 
import Sideline_Staff
import os
import sys
import Skaven_Roster, Wood_Elf_Roster, Amazon_Roster, Chaos_Chosen_Roster, Underworld_Roster,Black_Orcs_Roster, Dark_Elves_Roster, High_Elf_Roster, Lizardman_Roster, Necro_Roster, Nurgle_Roster, Orc_Roster, Goblins_Roster, Undead_Roster, Vampire_Roster, Tomb_Kings_Roster, Norse_Roster, Ogre_Roster, Dwarves_Roster, Human_Roster, Halfling_Roster, Nobs_Roster, Slann_Roster, Snotling_Roster, OWA_Roster, Gnome_Roster, Chaos_Dwarves_Roster, Elven_Union_Roster

choice = ''

roster_cost = 0 

def roster_choice():
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

def main_menu():
    global roster_cost
    print('-----Main Menu-----')
    print('1. View Roster')
    print('2. Adjust Roster')
    print('3. New Roster (will delete current roster)')
    print('4. Exit')
    selection = input('Select an option (1-4): ')
    if selection == '1':
        view_my_roster(load_roster(choice))
    elif selection == '2':
        adjust_roster(load_roster(choice))
    elif selection == '3':
        roster_cost = 0
        roster_choice()
        build_roster(load_roster(choice))
    elif selection == '4':
        sys.exit()
    else: 
        print('Invalid selection. Returning to main menu.')
        main_menu()

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
        print(f'{roster.roster_name}')
        print('----Sideline Staff----')
        if roster.Apothecary == True:
            print(f'Do you want to add an Apothecary for {Sideline_Staff.Apothecary}? (y/n)')
            response = input().lower()
            if response == 'y':
                f.write(f'Apothecary: {Sideline_Staff.Apothecary}\n')
                roster_cost += Sideline_Staff.Apothecary
        print(f'How many coaches for {Sideline_Staff.Coaches}?')
        coaches = int(input())
        if coaches >= 0 and coaches <= Sideline_Staff.max_count['Coaches']:
            f.write(f'Coaches: {coaches} x {Sideline_Staff.Coaches} = {coaches * Sideline_Staff.Coaches}\n')
            roster_cost += coaches * Sideline_Staff.Coaches
        else: 
            print('Invalid number of coaches. No coaches added.')
        print(f'How many cheerleaders for {Sideline_Staff.Cheerleaders}?')
        cheerleaders = int(input())
        if cheerleaders >= 0 and cheerleaders <= Sideline_Staff.max_count['Cheerleaders']:
            f.write(f'Cheerleaders: {cheerleaders} x {Sideline_Staff.Cheerleaders} = {cheerleaders * Sideline_Staff.Cheerleaders}\n')
            roster_cost += cheerleaders * Sideline_Staff.Cheerleaders
        else: 
            print('Invalid number of cheerleaders. No cheerleaders added.')
        print(f'How many rerolls would you like to add? ({roster.rerolls} each)')
        rerolls = int(input())
        if rerolls > 0: 
            f.write(f'Rerolls: {rerolls} x {roster.rerolls} = {rerolls * roster.rerolls}\n')
            roster_cost += rerolls * roster.rerolls
        else: 
            print('Invalid number of rerolls. No rerolls added.')

def roster_count(roster):
    global roster_cost
    global roster_cost
    print('----Players----')
    lines_to_write = []
    for pos in roster.Name:
        while True:
            try:
                count = int(input(f'How many {roster.Name[pos]} would you like to add? (Max {roster.Quantity[pos]}): '))
                break
            except ValueError:
                print('Please enter a valid integer.')
        if count < 0:
            print('Negative number entered. Zero added.')
            count = 0
        if count > roster.Quantity[pos]:
            print('Exceeds maximum quantity. Zero added.')
            count = 0

        lines_to_write.append(f'{roster.Name[pos]}: {count}, MA={roster.Stats[pos]["MA"]}, ST={roster.Stats[pos]["ST"]}, AG={roster.Stats[pos]["AG"]}, PA={roster.Stats[pos]["PA"]}, AV={roster.Stats[pos]["AV"]}\n')
        skills = roster.Skills.get(pos, [])
        lines_to_write.append(f'Skills: {", ".join(skills) if skills else "None"}\n')
        roster_cost += count * roster.Cost[pos]
    with open('Custom_Roster.txt', 'a') as f:
        f.writelines(lines_to_write)

    print(f'Current Roster Cost: {roster_cost}')
    print('Returning to main menu.')
    main_menu()

def adjust_roster(roster):
    global roster_cost
    try:
        with open('Custom_Roster.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print('No roster file found to adjust.')
        main_menu()
        return

    print('What position would you like to adjust? (Type the full position name or "exit" to return to main menu)')
    display_name = input().strip().lower()
    if display_name == 'exit':
        main_menu()
        return
    
    # Find the position key based on the display name
    pos = None
    for key in roster.Name:
        if roster.Name[key].lower() == display_name:
            pos = key
            break
    
    if pos is None:
        print('Invalid position. Please try again.')
        adjust_roster(roster)
        return

    # find existing line for the position
    found_index = None
    existing_count = 0
    for i, line in enumerate(lines):
        if line.startswith(f'{pos}:') or line.split(':', 1)[0].strip() == pos:
            found_index = i
            try:
                existing_count = int(line.split(':', 1)[1].split(',')[0].strip())
            except Exception:
                existing_count = 0
            break

    if found_index is None:
        print('Position not found in current roster.')
        main_menu()
        return

    while True:
        try:
            count = int(input(f'How many {roster.Name[pos]} would you like to have now? (Max {roster.Quantity[pos]}): '))
            break
        except ValueError:
            print('Please enter a valid integer.')

    if count < 0:
        print('Negative number entered. Zero used.')
        count = 0
    if count > roster.Quantity[pos]:
        print('Exceeds maximum quantity. Setting to maximum allowed.')
        count = roster.Quantity[pos]

    # update roster cost
    roster_cost -= existing_count * roster.Cost[pos]
    roster_cost += count * roster.Cost[pos]

    # replace the line
    lines[found_index] = f'{pos}: {count}, MA={roster.Stats[pos]["MA"]}, ST={roster.Stats[pos]["ST"]}, AG={roster.Stats[pos]["AG"]}, PA={roster.Stats[pos]["PA"]}, AV={roster.Stats[pos]["AV"]}\n'

    with open('Custom_Roster.txt', 'w') as f:
        f.writelines(lines)

    print('Adjustment saved.')
    main_menu()

def view_my_roster(roster):
    with open ('Custom_Roster.txt', 'r') as f:
        print(f.read())


roster_choice()
load_roster(choice)
display_roster(load_roster(choice))

