import random
import time

#star variables
i = 0
a = 0
b = 0 
t = 0
balance = 700

#main loop
while i == 0:
    #bet
    while a == 0: 
        print(f"this is your balance: {balance}")
        time.sleep(1)
        bet = int(input("type the amount you want to bet"))
        if balance >= bet and bet>0: 
            balance -= bet
            a = 1
        elif balance <  bet:
            print("the amount you want to bet is bigger than your balance")
            time.sleep(1)
        elif bet < 0:
            print("you cant bet a negative amount")
            time.sleep(1)
        time.sleep(1)
        a = 0
        
        #Cards
        cards=[2,3,4,5,6,7,8,9,10,10,10,10,11]
        Hcards=[1,2,3,4,5,6,7,8,9,10,10,10,10,11]
        rand1= random.randint(0,12)
        rand2 = random.randint(0,12)
        fist_card = cards[rand1]
        second_card = cards[rand2]
        total  =fist_card + second_card
        print("shuffling the deck")
        time.sleep(2)
        print(f"you get a")
        time.sleep(1)
        print(f"{fist_card}")
        time.sleep(1)
        print("and")
        time.sleep(1)
        print(f"{second_card}")
        time.sleep(1)
        
        #Show totals depending if he gets n As or not
        if not fist_card == 11 and not second_card == 11:
            total= fist_card + second_card
            print (f"your total is {total}")
        if fist_card == 11:
            total1 = 1 + second_card
            total2 = 11 + second_card
            print(f"You get an As your total can be {total1} or {total2} ")
            
            if second_card == 11:
                total = fist_card + 1
                total2 = fist_card + 11
            print(f"You get an As your total can be {total1} or {total2} ")
        all_cards = []
        time.sleep(1)
        rand_House1 = random.randint(0,13)
        house_cards1 = Hcards[rand_House1]
        print(f"the house gets a {house_cards1}")
        time.sleep(1)
        #Mora Cards
        while b == 0:
            another_card = int(input("type 1 if you want to draw another card or 0 if you want to stay"))
            if another_card == 1:
                randanotherone= random.randint(0,12)
                the_otherone = cards[randanotherone]
                print(f"you get a{the_otherone}")
                time.sleep(1)
                if the_otherone ==11:
                    print("You just get an as, what value do you want to set?, type 1 or 11")
                    value_as= int(input(": "))
                    if value_as == 1:
                        the_otherone = 1
                    else:
                        the_otherone =11
                    all_cards.append(the_otherone)
                    
                    time.sleep(1)
                    
                    if another_card == 0:
                        b = 1
                b = 0
        
        if fist_card == 11:
            print("you get an as in your fist card, what value do you want to set?, type 1 or 11")
            value_as= int(input(": "))
            if value_as == 1:
                fist_card = 1
        else:
            fist_card=11
    if second_card ==11:
        print("you get an as in your second card, what value do you want to set?, type 1 or 11")
        value_as= int(input(": "))
        if value_as == 1:
            second_card = 1
        else:
            second_card = 11
    all_cards.append(fist_card)
    all_cards.append(second_card)
    time.sleep(1)
    totalEx = sum(all_cards)
    time.sleep(1)
    print(f"these are your cards(all_cards)")
    time.sleep(1)
    print(f"ypur official total is {totalEx}")
    time.sleep(2)
    print(f"Now the house plays")
    time.sleep(1)
    #draw on 16 stay 17
    print(f"the fist card of the house was {house_cards1}")
    rand_House2 = random.randint(0,13)
    house_cards2 = cards[rand_House2]
    time.sleep(1)
    print(f"the house get a {house_cards2}")
    all_cardsHouse=[]
    all_cardsHouse.append(house_cards1)
    all_cardsHouse.append(house_cards2) 
    house_total = house_cards1 + house_cards2
    time.sleep(1)
    
    while house_total <= 16:
        rand_anotherHouse = random.randint(0,12)
        another_House = cards[rand_anotherHouse]
        all_cardsHouse.append(another_House)
        house_total += another_House
        print (f"the house request and gets {another_House}")
        time.sleep(1)
        totalExHouse = sum(all_cardsHouse)
        time.sleep(2)
        print(f"you result was {totalEx} and the house result was {totalExHouse}")
        time.sleep(2)
        #example results me 16 machine 18
        if (totalEx > 21 and totalExHouse > 21) or (totalEx == totalExHouse and not totalEx > 21 and totalExHouse > 21):
            win = bet
            balance += win
            print=("tie, no one wins")
        elif totalEx <= totalExHouse <= 21:
            print("you lose")
        elif totalExHouse < totalEx <=21:
            win = bet * 2
            balance += win
            print(f"you win {win}")
        elif  totalEx <= 21 < totalExHouse:
            win=bet * 2
            balance += win
            print(f"you win {win} ")
        else:
            print("you lose")
            
        