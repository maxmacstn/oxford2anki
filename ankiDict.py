import requests
import json
import sys
import getopt
import re
from credentials import *




language = 'en-gb'
fields = 'definitions,examples'
strictMatch = 'false'

# Get lemmas (root word) from the API 
def getLemmas(word_id):
    url = 'https://od-api.oxforddictionaries.com:443/api/v2/lemmas/' + \
        language + '/' + word_id.lower()
    r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})
    return r

# Get the meaning (definitions, examples) from the API
def getEntries(word_id):
    url = 'https://od-api.oxforddictionaries.com:443/api/v2/entries/' + language + \
        '/' + word_id.lower() + '?fields=' + fields + '&strictMatch=' + strictMatch;

    r = requests.get(url, headers={'app_id': app_id, 'app_key': app_key})

    print("Translate "+word_id, end="\t")
    
    if (r.status_code != 200):
        if(r.status_code == 404):
            lemmasResponse = getLemmas(word_id)
            if (lemmasResponse.status_code == 200):
                rootWord = json.loads(lemmasResponse.text)[
                                      "results"][0]["lexicalEntries"][0]["inflectionOf"][0]["id"]
                if (rootWord == word_id):
                    print("Error : No root found")
                    return None

                print("-->  " + rootWord)
                return getEntries(rootWord)

        print("Error : " + str(r.status_code))
        return None

    else:
        print("OK")
    return r.text

# Convert sense to HTML format
def getSenseHTML(sense, number=0, subsense=False):

    html = ""

    if (not subsense):
        html += "<div>"+str(number)+". " if number else "<div>"
    else:
        html += "<p style = \"text-indent : 1em;\"> •"

    if (sense.get("definitions") is not None):
        for definition in sense["definitions"]:
            html += definition

    if (sense.get("examples") is not None):
        html += ": "
        html += "<span style=\"font-style: italic;\">"
        for i in range(len(sense["examples"])):
            if i:
                html += " | "
            html += sense["examples"][i]["text"]
        html += "</span><br>"

    if (sense.get("subsenses") is not None):
        for subsense in sense["subsenses"]:
            html += getSenseHTML(subsense, subsense=True)

    if not subsense:
        html += "</div><br>"
    else:
        html += "</p>"

    return html

# Convert lexical entry to HTML format
def getLexicalEntryHTML(lexicalEntry):
    html = "<div><u>" + \
        lexicalEntry["lexicalCategory"]["text"].lower()+"</u></div>"
    senseIndex = 1;

    for entry in lexicalEntry["entries"]:
        for sense in entry["senses"]:
            html += getSenseHTML(sense,
                             senseIndex if len(entry["senses"]) > 1 else 0)
            senseIndex += 1

    return html

# convert each entry from result to HTML format
def getFormattedHTMLResult(result, superscript=0):
    html = "<b>"+result["word"] + "<sup>"+str(
        superscript)+"</sup></b>" if superscript else "<b>"+result["word"] + "</b>"
    for lexicalEntry in result["lexicalEntries"]:
        html += getLexicalEntryHTML(lexicalEntry)

    return html

# convert each response from response to HTML format (Each word might have multiple homograph)
def getFormattedHTMLResponse(jsonResponse):
    html = ""
    homographIndex = 1
    for result in jsonResponse:
        html += getFormattedHTMLResult(result,
                                   homographIndex if len(jsonResponse) > 1 else 0)
        homographIndex += 1

    return html


def convertFileToAnkiDeck(input, output="ankiDictDeck.txt"):
    inputFile = open(input, 'r')
    outputFile = open(output, 'w')

    Lines = inputFile.readlines()
    for line in Lines:
        word = line.strip().lower()
        word = re.sub(r"[^A-Za-z]+", '', word)
        if(len(word) <= 1):
            continue
        
        result = getEntries(word)
        if result is None:
            continue
            
        jsonResult = json.loads(result)
        wordID = jsonResult["id"]
        definitionHTML = getFormattedHTMLResponse(jsonResult["results"]) 

        # writing to file 
        outputFile.writelines(wordID +"\t"+definitionHTML+"\n") 
    
    inputFile.close() 


def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
        if len(opts) == 0:
            raise getopt.GetoptError("please enter options")
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('dict2Anki -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg


    if (len(outputfile)):
        convertFileToAnkiDeck(inputfile,outputfile)
    else:
        convertFileToAnkiDeck(inputfile)
 

if __name__ == "__main__":
   main(sys.argv[1:])


# convertFileToAnkiDeck("words.txt")




