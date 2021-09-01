import random


def RangeCat():
    Cat=random.randrange(1, 16)
    return Cat

def CatText():
    Cat=RangeCat()
    Catext={}
    for i in range(Cat):
        Porc=random.random()
        Categ=letter()
        Catext[Categ]=round(Porc,2)
    return Catext

def CatMetadata():
    Cat=RangeCat()
    Catext={}
    for i in range(Cat):
        Porc=random.random()
        Categ=letter()
        Catext[Categ]=round(Porc,2)
    return Catext
def CatImage():
    Cat=RangeCat()
    
    Catext={}
    for i in range(Cat):
        Porc=random.random()
        Categ=letter()
        Catext[Categ]=round(Porc,2)
    return Catext

def letter():
       return random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

def outputs():
    DicText=CatText()
    DicMetadata=CatMetadata()
    DicImage=CatImage()
    Close={"Text":DicText,"Metadata":DicMetadata,"Image":DicImage}
    return Close
if __name__ == '__main__':
   
  print(outputs())
    