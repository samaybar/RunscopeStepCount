import requests
import array
import json
import csv

filename = "TestDetails.csv"

fields = ['BucketName','JobName','Steps','PublicLocations','PublicLocation_Count','PrivateLocations','PrivateLocation_Count','Interval']

BucketsURL = "https://api.runscope.com/buckets"



params = {'output': 'JSON'}   
headers = {'Authorization': 'Bearer TOKENGOESHERE'}


def get_bucket_tests(Bucket, offset):
        TestListURL = BucketsURL+"/"+str(Bucket["key"])+"/tests?count=100&offset="+str(offset)
        TestListDetail = requests.get(TestListURL,headers=headers,params=params) 
        TestListData = json.loads(TestListDetail.text)
        TestList = TestListData["data"]
        

        for test in TestList:
            TestDetailURL = BucketsURL+"/"+str(Bucket["key"])+"/tests/"+str(test["id"])
            TestDetail = requests.get(TestDetailURL,headers=headers,params=params)
            TestDetailData = json.loads(TestDetail.text)
            TestData = TestDetailData["data"]
            steps = TestData["steps"]
            stepscount=str(len(steps))           
            BucketName = Bucket["name"]
            TestName= TestData["name"]
            
            locations = TestData["environments"]
            
            schedules = TestData["schedules"]

            if(len(schedules)>0):
                 for schedule in schedules:
                     #print(schedule)
                     EnvironmentURL = BucketsURL+"/"+str(Bucket["key"])+"/environments/"+str(schedule["environment_id"])
                     #print(EnvironmentURL)
                     EnvironmentDetail = requests.get(EnvironmentURL,headers=headers,params=params)
                     EnvironmentDetailData = json.loads(EnvironmentDetail.text)
                     EnvironmentData = EnvironmentDetailData["data"]
                     detail=[]
                     detail.append(BucketName)
                     detail.append(TestName)
                     detail.append(stepscount)
                     Private_locations=""
                     Public_locations=""
                     Publiclocation_count = len(EnvironmentData["regions"])
                     Privatelocation_count = len(EnvironmentData["remote_agents"])
                     if(len(EnvironmentData["regions"])>0):
                         Public_locations = str(EnvironmentData["regions"][0])    
                         for j in range(1,Publiclocation_count):                        
                             Public_locations = Public_locations + "," + str(EnvironmentData["regions"][j])
                     if(len(EnvironmentData["remote_agents"])>0):
                         Private_locations = str(EnvironmentData["remote_agents"][0])    
                         for k in range(1,Privatelocation_count):                        
                             Private_locations = Private_locations + "," + str(EnvironmentData["remote_agents"][k])


                     #we need to include locations from parent environment
                     ParentEnvironment = EnvironmentData["parent_environment_id"]
                     if ParentEnvironment is not None:
                         ParentEnvironmentURL = BucketsURL+"/"+str(Bucket["key"])+"/environments/"+str(ParentEnvironment)
                         ParentEnvironmentDetail = requests.get(ParentEnvironmentURL,headers=headers,params=params)
                         ParentEnvironmentDetailData = json.loads(ParentEnvironmentDetail.text)
                         ParentEnvironmentData = ParentEnvironmentDetailData["data"]
                         Publiclocation_count = Publiclocation_count + len(ParentEnvironmentData["regions"])
                         Privatelocation_count = Privatelocation_count + len(ParentEnvironmentData["remote_agents"])
                         if(len(ParentEnvironmentData["regions"])>0):
                            Public_locations = Public_locations + "," + str(ParentEnvironmentData["regions"])
                             #Public_locations = Public_locations + "," + str(ParentEnvironmentData["regions"][0])    
                             #for x in range(1,Publiclocation_count):                        
                              #   Public_locations = Public_locations + "," + str(ParentEnvironmentData["regions"][x])
                         if(len(ParentEnvironmentData["remote_agents"])>0):
                            Private_locations = Private_locations + "," + str(ParentEnvironmentData["remote_agents"])
                            # Private_locations = Private_locations + "," + str(ParentEnvironmentData["remote_agents"][0])    
                            # for y in range(1,Privatelocation_count):                        
                                # Private_locations = Private_locations + "," + str(ParentEnvironmentData["remote_agents"][y])

                     if(Publiclocation_count==0):
                         Public_locations = "not used"

                     detail.append(Public_locations)
                     detail.append(Publiclocation_count)

                     if(Privatelocation_count==0):
                         Private_locations = "not used"

                     detail.append(Private_locations)
                     detail.append(Privatelocation_count)
                     detail.append(schedule["interval"])
                     csvwriter.writerow(detail)
                     print(detail)

            else:
                detail=[]
                detail.append(BucketName)
                detail.append(TestName)
                detail.append(stepscount)
                detail.append("no schedules")
                detail.append("0")
                detail.append("no schedules")
                detail.append("0")
                detail.append("no schedules")
                csvwriter.writerow(detail)
                print(detail)
        if(len(TestList)==100):
            offset = offset+100
            get_bucket_tests(Bucket, offset)



Buckets = requests.get(BucketsURL, headers=headers, params=params)


BucketsList = json.loads(Buckets.text)

with open(filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
        
    for Bucket in BucketsList["data"]:
        get_bucket_tests(Bucket,0)

