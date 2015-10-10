import numpy as np
import time

TYPES = ['Unknown', 'One-of', 'Monthly', 'Daily', 'Yearly']
TYPES2 = ['', 'Day', 'Months', 'Days', 'Years']

# Customer class makes handling each customer easier.


class Customer:

    def __init__(self, Id):
        # Every customer has an Id (subscription ID),
        # a list of all their purchases in the form
        #(Amount, (Month/Day/Year)), and a type.
        self.Id = Id
        self.purchases = []
        self.type = 0

    # Easy function for adding purchases.
    def addPurchase(self, purchase):
        self.purchases.append(purchase)

    def __repr__(self):
        return str(self.Id) + ' - ' + str(self.purchases)


def main():

    # A lot of the code here is just for benchmarking purposes, the main
    # parts are in their own functions.
    dataFile  = 'subscription_report.csv'
    print('Reading ' + dataFile + '...')
    startTime = time.perf_counter()
    initialTime = startTime
    # This is the first main code, which reads the CSV and
    # reads the file's data into memory - one list with all
    # the purchases, and one with the revenues for each
    # year.
    purchaseList, annualRevenues = readCSV(dataFile)

    duration = getTime(startTime)
    print('Reading finished in ' + str(duration) + 's, identifying types...')

    startTime = time.perf_counter()
    # Second main code, this function takes the purchases that
    # are in memory and generates a list of unique Customer
    # objects for each unique customer identified from the list
    # of purchases, then identifies what type they are according
    # to their purchases.
    customerList = identifyCustomers(purchaseList)
    duration = getTime(startTime)
    print('Identification took ' + str(duration) + 's')

    print('Calculating delta revenues and future revenues...')
    # Calculates future revenue based on the identified
    # customers
    futureRevenue = calculateRevenue(customerList)
    # Calculates the top 2 and bottom 2 consecutive years that had the
    # highest or lowest increase/decrease in revenue.
    d1, d2, i1, i2 = calculateDerivatives(annualRevenues)
    print('Finished.')

    duration = getTime(initialTime)
    print('Took a total of ' + str(duration) + 's')

    startTime = time.perf_counter()
    print('Writing to output.txt')

    # The rest of the code just reads the data from the Customer
    # objects and writes them to an output file, as well as
    # annual revenues and predicted revenues.
    outputFile = open('output.txt', 'w')
    print('Sub ID\tType\tLength\n', file=outputFile)
    for customer in customerList:
        print(customer.Id, TYPES[customer.type], str(
            len(customer.purchases)) + ' ' + TYPES2[customer.type], sep='\t', file=outputFile)
    print('\nAnnual Revenues\nYear\tAmount(USD)', file=outputFile)
    for year, amount in enumerate(annualRevenues):
        print(str(year + 1966) + '\t$' + format(amount, ',d'), file=outputFile)
    print('\nHighest Decreases in Revenue', file=outputFile)
    print('{}-{} ${:,d}'.format(*d1),
          '{}-{} ${:,d}'.format(*d2), sep='\n', file=outputFile)
    print('\nHighest Increases in Revenue', file=outputFile)
    print('{}-{} $+{:,d}'.format(*i1),
          '{}-{} $+{:,d}'.format(*i2), sep='\n', file=outputFile)
    print('\nPredicted Revenue for 2015: $' +
          format(futureRevenue, ',d'), file=outputFile)
    outputFile.close()
    duration = getTime(startTime)
    print('Finished writing in ' + str(duration) + 's')

# readCSV is very simple, just reads all the data from a file
# and returns a list with all the purchases, and another list
# with each years annual revenues.
def readCSV(fname: str, limit: int=None) -> tuple:
    i = 0
    purchaseList = []
    annualRevenues = [0] * 49
    file = open(fname, 'r')
    # Discard first line
    file.readline()
    for line in file:
        info = parse(line)
        Id, sId, Amt, Date = info
        # We discard the ID when we add to list of purchases,
        # as it is not useful for any algorithm.
        purchaseList.append(info[1:])
        # This is where the annual revenues get tallied.
        annualRevenues[Date[2] - 1966] += Amt
        i += 1
        if limit and (i > limit):
            break
    file.close()
    return purchaseList, annualRevenues


# parse is the function that converts strings like
#'1234,2313,490,(1/11/1966)' to actual data in a tuple.
def parse(text: str) -> tuple:
    data = text.strip().split(',')
    # It returns a tuple in the format ( Id,SubId,Amount,(Month,Day,Year) )
    return tuple(map(int, data[:-1])) + (tuple(map(int, data[-1].split('/'))),)


# identifyCustomers is where most of the algorithm lies,
# although it is quite simple.
def identifyCustomers(purchaseList: list) -> list:

    # First the purchase list is sorted by the subscription ID.
    # this is quite fast, taking only 1-2 seconds. The goal is to
    # group all identical subscription ID's together.

    purchaseList.sort(key=lambda obj: obj[0])  # sort by ID

    # Here we put the first purchase in the list to start off
    # the algorithm that collects unique Customers.
    # This is required for the algorithm to start.
    currentId = purchaseList[0][0]
    newCustomer = Customer(currentId)
    uniqueCustomers = [newCustomer]

    # A simple algorithm that may look a bit complicated, all this does
    # in essence is collapse the purchase list into a smaller list of
    # Customer objects, where each customer is attributed their purchases.
    # It essentially converts a list of purchases to a list of customers
    # with purchases.
    for purchase in purchaseList:
        # if the current purchase belongs to the customer's ID we
        # are still on, add it to their purchases.
        if (purchase[0] == currentId):
            uniqueCustomers[-1].addPurchase(purchase[1:])
        # otherwise, we have encountered a new customer, so we
        # create a new Customer object for it and add
        # this purchase.
        else:
            currentId = purchase[0]
            newCustomer = Customer(currentId)
            newCustomer.addPurchase(purchase[1:])
            uniqueCustomers.append(newCustomer)

    # This is the algorith that acttualy identifies what type the customers
    # are.
    for customer in uniqueCustomers:
        # if the customer has only one purchase, they are one-of.
        if len(customer.purchases) == 1:
            customer.type = 1
        else:
            # Otherwise, use an algorithm to detect the customer's type using
            # purchase dates and set it.
            customer.type = detectSequence(
                [date for amount, date in customer.purchases])

    return uniqueCustomers


# This function determines the type of the customer
def detectSequence(seq: list) -> int:
    # extract consecutive days, months and years into
    # their own lists
    days = [date[1] for date in seq]
    months = [date[0] for date in seq]
    years = [date[2] for date in seq]

    # If a customer subscribes everyday for any number
    # of consecutive days greater than 1, they are daily customers.
    if isContinuous(days):
        return 3  # Daily
    # If a customer subscribes for any number of consecutive months
    # greater than 1, they are monthly customers.
    if isContinuous(months):
        return 2  # Monthly
    # The yearly detection is the simplest, as there is no looping
    # to worry about. The algorithm simply detects that the customer
    # subscribes every year for a number of consecutive years greater than 1.
    if isConsecutive(years):
        return 4  # Yearly

    # An important thing to note is the order in which they are identified,
    # as daily customers and monthly customers have consecutive years, and
    # daily customers have consecutive months, etc. So it is important to do
    # it in this order to correctly identify what type they are. This works
    # because while daily customers have consecutive years, yearly customers
    # do not have consecutive days, as they purchase on the same day,month every
    # year. This is true for monthly customers as well, purchasing on the same
    # day.

    return 0  # Unknown

# the isContinuous function checks if a list is consecutive (increasing by 1 each time)
#, or if it's not,
# it checks whether a sublist in the list going from index 0 to the first max
# is coherent. This is done because sometimes daily purchases go past a month, and
# monthly purchases go past a year, creating breaks which are not coherent.
# This algorithm assumes that if a customer bought continuously each day for one month,
# or continuously each month for a year, they would continue to do so. This is safe
# to assume given a customer is said to have only one definitive type and no
# mixed behaviour.
def isContinuous(l: list) -> bool:
    return (isConsecutive(l) or isConsecutive(l[:firstMax(l) + 1]))

# Helper function for calculating algorithm speeds.
def getTime(startTime: float) -> float:
    return time.perf_counter() - startTime

# uses numpy to easily calculate whether a sequence is consecutive,
# that is, if it's increasing by 1 each time.
def isConsecutive(l: list) -> bool:
    return all(np.diff(np.array(l)) == 1)

# A helper function to format dates into readable format.
def getDate(purchase: tuple) -> str:
    return '/'.join(str(n) for n in purchase[1])

# returns the position of the first maximum in a list.
def firstMax(l: list) -> int:
    _max = -float('inf')
    _maxIndex = 0
    for i, e in enumerate(l):
        if (e >= _max):
            _max = e
            _maxIndex = i
        else:
            break
    return _maxIndex

# Calculates predicted revenue for 2015 based on
# retaining customers in 2014 and their subscription
# type.
def calculateRevenue(customerList: list) -> int:
    predictedValue = 0
    for customer in customerList:
        # extract consecutive days, months and years into
        # their own lists
        lastPurchaseDate = customer.purchases[-1][1]
        # the amount they pay each time
        subscription = customer.purchases[0][0]

        if (lastPurchaseDate[2] == 2014):  # made a purchase in 2014
            if (customer.type == 4):  # yearly
                predictedValue += subscription
            # made a purchase in last month of 2014
            if (lastPurchaseDate[0] == 12):
                if (customer.type == 2):  # monthly
                    predictedValue += subscription * 12
                # made a purchase in last day of 2014
                if (lastPurchaseDate[1] == 31):
                    if (customer.type == 3):  # daily
                        predictedValue += subscription * 365
        # one-of customers are ignored.

    return predictedValue

# amount is the amount of year ranges returned. eg. amount=3 returns the
# top 3 highest increase and top 3 highest decrease
def calculateDerivatives(annualRevenues: list, amount: int=2) -> tuple:
    arr = np.array(annualRevenues)
    # calculates the differences between the years
    diffs = np.diff(arr)

    # sorts differences by value but returns indexes instead of values.
    sortedIndexes = np.argsort(diffs)
    # regular sort
    sortedValues = sorted(diffs)

    # finds highest increases and decreases and returns
    # in the form (start year, end year, amount)

    # yield the bottom 2
    for i in range(amount):
        yield (sortedIndexes[i] + 1966, sortedIndexes[i] + 1966 + 1, sortedValues[i])
    # yield the top 2
    for i in range(amount):
        yield (sortedIndexes[-(i + 1)] + 1966, sortedIndexes[-(i + 1)] + 1966 + 1, sortedValues[-(i + 1)])


if __name__ == '__main__':
    main()
