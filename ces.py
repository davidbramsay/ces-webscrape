from urllib2 import urlopen, HTTPError
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from string import ascii_lowercase
import pickle
import time
import re

'''
#would work if it was a static page, but alas

def getTable(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html.read())
        table = bsObj.find("table",{"id":"jq-featured-exhibitors"})
        table2 = bsObj.find("table",{"jq-regular-exhibitors"})
        print bsObj
    except AttributeError as e:
        return None
    return table, table2

t1, t2 = getTable("http://ces17.mapyourshow.com/7_0/alphalist.cfm?alpha=A")
if t1 == None or t2 == None:
    print("Table could not be found")
else:
    print("----------------------------------------")
    for row in t1.tr.next_siblings:
        print(row)
    print("----------------------------------------")
    for row in t2.tr.next_siblings:
        print(row)
'''



def getDescription(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html.read(), "html.parser")
        description = bsObj.find("div", {"class":"mys-taper-measure"}).text
        description = description.strip() #remove leading/trailing spaces
        description = re.sub('\s+',' ', description) #replace tabs/newlines with spaces
    except:
        return None

    return description



def getAllExhibitorsWithLetter(letter = "A"):
    letter = letter.upper()
    cesString = "http://ces17.mapyourshow.com/7_0/alphalist.cfm?alpha=" + letter

    driver = webdriver.Chrome()
    driver.get(cesString)

    try:
        #wait for table to load
        WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "jq-regular-exhibitors")))
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")

    finally:
        #scroll to bottom to load all of table
        match=False
        while(match==False):
            lastCount = lenOfPage
            time.sleep(3)
            lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            if lastCount==lenOfPage:
                match=True

        #pull out values from table
        table1 = driver.find_element_by_id("jq-regular-exhibitors")
        table1vals = table1.find_elements_by_tag_name("a")

        featured_exists = True
        try:
            table2 = driver.find_element_by_id("jq-featured-exhibitors")
            table2vals = table2.find_elements_by_tag_name("a")
        except:
            featured_exists = False


        #format into a list of dicts
        full_list = []
        new_item = {"location": []}
        i=0
        while (i < len(table1vals)):
            link = table1vals[i].get_attribute('href')

            if 'exhibitor' in link:

                if new_item['location'] != []:
                    full_list.append(new_item)
                    print 'added ' + new_item['name'] + '...'

                new_item = {"location": []}
                new_item["name"] = table1vals[i].text
                new_item["link"] = link
                new_item["desc"] = getDescription(link)

            elif 'floorplan_link' in link:
                new_item["location"].append(table1vals[i].text)

            i+=1


        if featured_exists:

            new_item = {"location": []}
            i=0
            while (i < len(table2vals)):
                link = table2vals[i].get_attribute('href')

                if 'exhibitor' in link:

                    if new_item['location'] != []:
                        full_list.append(new_item)
                        print 'added ' + new_item['name'] + '...'

                    new_item = {"location": []}
                    new_item["name"] = table2vals[i].text
                    new_item["link"] = link
                    new_item["desc"] = getDescription(link)

                elif 'floorplan_link' in link:
                    new_item["location"].append(table2vals[i].text)

                i+=1


        driver.close()

        print "Found ", len(full_list), " entries for", letter,  "."
        return full_list



def saveExhibitorFile(letter = "A", filenameprefix = "cesData"):
    letter = letter.upper()
    filename = filenameprefix + letter + ".pickle"
    data = getAllExhibitorsWithLetter(letter)
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print "wrote to file: ", filename
    except:
        print "Failed to write to pickle"



def openExhibitorFile(letter = "A", filenameprefix = "cesData"):
    letter = letter.upper()
    filename = filenameprefix + letter + ".pickle"
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
    except:
        print "Failed to write to pickle"

    print "loaded file: ", filename
    return data



class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'



def prettyPrint(data):

    '''
    stringVersion = json.dumps(data, default=lambda o: o.__dict__)
    jsonVersion = json.loads(stringVersion)
    print json.dumps(jsonVersion, indent=4)
    '''

    for row in data:
        if row['desc'] is not None:
            #print row['name'] + u' || ' + row['desc'] + u' || ' + u",".join(row['location'])
            outstring = color.BOLD + color.GREEN + color.UNDERLINE + row['name'] + \
                    color.END + u': ' + row['desc'] + \
                    color.YELLOW + u' ...' + u", ".join(row['location']) + '\n'

            print outstring.encode('utf-8')



def prettyPrintByLocation(data):

    tempval = ''
    for row in data:
        if row['desc'] is not None:

            outstring = color.BOLD + color.GREEN + color.UNDERLINE + row['name'] + \
                    color.END + u': ' + row['desc'] + \
                    color.YELLOW + u' ...' + u", ".join(row['location']) + '\n'

            if tempval[0:2] != row['location'][0][0:2] or len(tempval) != len(row['location'][0]):
                print '\n---------------\n'

            tempval = row['location'][0]

            print outstring.encode('utf-8')
        else:
            outstring = color.BOLD + color.GREEN + color.UNDERLINE + row['name'] + \
                    color.END + u': no description provided :(' + \
                    color.YELLOW + u' ...' + u", ".join(row['location']) + '\n'

            if tempval[0:2] != row['location'][0][0:2] or len(tempval) != len(row['location'][0]):
                print '\n---------------\n'

            tempval = row['location'][0]

            print outstring.encode('utf-8')



def prettyPrintNoFormat(data):

    tempval = ''
    for row in data:
        if row['desc'] is not None:

            outstring = row['name'] + \
                    u': ' + row['desc'] + \
                    u' ...' + u", ".join(row['location']) + '\n'

            if tempval[0:2] != row['location'][0][0:2]:
                print '\n---------------\n'

            tempval = row['location'][0]

            print outstring.encode('utf-8')




if __name__ == "__main__":

    '''
    #scrape all the data and save it in pickles
    for letter in ascii_lowercase:
        saveExhibitorFile(letter)
    '''

    '''
    #open data and print it all
    for letter in ascii_lowercase:
        data = openExhibitorFile(letter)
        prettyPrint(data)
    #write to file, do:
    # >>  python ces.py > out.txt
    # >>  cat out.txt
    '''

    dataset = []
    for letter in ascii_lowercase:
        dataset.extend(openExhibitorFile(letter))

    sorteddata = sorted(dataset, key=lambda k: k['location'][0])
    prettyPrintByLocation(sorteddata)
    #prettyPrintNoFormat(sorteddata)
    #prettyPrint(sorteddata)

    '''
    letters = ['a','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    for letter in letters:
        try:
            saveExhibitorFile(letter)
        except:
            print "FAILED TO PRINT " + letter
    '''
