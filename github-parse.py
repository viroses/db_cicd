import os
import sys
import json
import requests
from operator import eq
import collections

if __name__ == "__main__":

    PERSONAL_ACCESS_TOKEN = sys.argv[1]
    COMMIT_ID = sys.argv[2]

    # Get commit information
    headers = {
        'Authorization': 'token ' + PERSONAL_ACCESS_TOKEN,
    }
    response = requests.get('https://api.github.com/repos/viroses/db_cicd/commits/' + COMMIT_ID, json=[], headers=headers)
    
    # Convert Byte to String
    message = response.content.decode('utf-8')

    # Convert it to JSON
    files = json.loads(message)["files"][0]
    
    # Extract values I need
    fileName = files["filename"]
    changes = files["changes"]
    additions = files["additions"]
    deletions = files["deletions"]
    patch = files["patch"]

    targetStatement = ""

    if(eq(fileName[len(fileName)-4:], ".sql")):
        # This is table
        if(changes == additions):
            # create table
            if(int(patch.split(',')[1][0:1]) < 1):
                targetStatement = "mysql -h mysql-master.custom-db.com -u tester -D db_cicd -e \""
                temp = patch.split('\n')
                del temp[0]
                for stmt in temp:
                    targetStatement += str(stmt).lstrip('+').lstrip()
                targetStatement += "\""
            # add column
            else:
                for stmt in patch.split('\n'):
                    if(stmt[0:1] == '+'):
                        targetStatement = ("pt-online-schema-change --alter \"add column " + 
                        str(stmt).lstrip('+').lstrip().rstrip(',') + "\" " + 
                        "D=db_cicd,t=" +
                        str(patch.split('\n')[1]).upper().lstrip('CREATE TABLE').rstrip('(').strip() + 
                        " --host=mysql-master.custom-db.com --port=3306 --user=tester --execute")
                        break   
        elif(changes == deletions):
            # drop table
            if(int(patch.split(',')[2][0:1]) < 1):
                targetStatement = ("mysql -h mysql-master.custom-db.com -u tester -D db_cicd -e \"drop table " + 
                                str(patch.split('\n')[1]).upper().lstrip('-CREATE TABLE ').rstrip('(').strip() + ";\"")
            # drop column
            else:
                for stmt in patch.split('\n'):
                    if(stmt[0:1] == '-'):
                        targetStatement = ("pt-online-schema-change --alter \"drop column " + 
                                        str(stmt).lstrip('-').lstrip().rstrip(',').split( )[0] + "\" " + 
                                        "D=db_cicd,t=" +
                                        str(patch.split('\n')[1]).upper().lstrip('CREATE TABLE ').rstrip('(').strip() + 
                                        " --host=mysql-master.custom-db.com --port=3306 --user=tester --execute")
                        break
        elif(changes == (additions+deletions)):
            # modify column
            for stmt in patch.split('\n'):
                if(stmt[0:1] == '+'):
                    targetStatement = ("pt-online-schema-change --alter \"modify column " + 
                    str(stmt).lstrip('+').lstrip().rstrip(',') + "\" " + 
                    "D=db_cicd,t=" +
                    str(patch.split('\n')[1]).upper().lstrip('CREATE TABLE ').rstrip('(').strip() + 
                    " --host=mysql-master.custom-db.com --port=3306 --user=tester --execute")
                    break
    else:
        # this is not a table
        targetStatement = "mysql --version"
    
    print(targetStatement)
    os.system(targetStatement)
