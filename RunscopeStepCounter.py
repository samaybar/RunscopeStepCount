import requests
import array
import json
import csv
import sys

filename = "TestDetails.csv"

fields = ['BucketName','JobName','TestURL','Steps','PublicLocations','PublicLocation_Count','PrivateLocations','PrivateLocation_Count','Interval']

BucketsURL = "https://api.runscope.com/buckets"



params = {'output': 'JSON'}   
headers = {'Authorization': 'Bearer TOKENGOESHERE'}
if (len(sys.argv)>1):
    authToken = "Bearer " + sys.argv[1] 
    headers = {'Authorization': authToken}

def count_steps(Steps):
    stepCount = 0
    #print(stepCount)
    for step in Steps:
        #print(step["step_type"])
        if(step["skipped"]==False):
            if(step["step_type"]=="request" or step["step_type"]=="inbound" or step["step_type"]=="ghost-inspector"):
                stepCount += 1
            elif(step["step_type"]=="condition"):

                stepCount = stepCount + count_steps(step["steps"])
            elif(step["step_type"]=="subtest"):
                stepCount += 1
                SubtestDetailURL = BucketsURL+"/"+str(step["bucket_key"])+"/tests/"+str(step["test_uuid"])
                SubtestDetail = requests.get(SubtestDetailURL,headers=headers,params=params) 
                SubtestDetailData = json.loads(SubtestDetail.text)
                if(SubtestDetailData["error"] is not None):
                    stepCount = stepCount
                    print("subtest is deleted - test will not run")
                else:
                    SubtestData = SubtestDetailData["data"]
                    #print(SubtestData)
                    stepCount = stepCount + count_steps(SubtestData["steps"])
            else:
                stepCount = stepCount
    #print(stepCount)
    return stepCount


def get_bucket_tests(Bucket, offset):
        TestListURL = BucketsURL+"/"+str(Bucket["key"])+"/tests?count=100&offset="+str(offset)
        TestListDetail = requests.get(TestListURL,headers=headers,params=params) 
        TestListData = json.loads(TestListDetail.text)
        TestList = TestListData["data"]
        

        for test in TestList:
            TestDetailURL = BucketsURL+"/"+str(Bucket["key"])+"/tests/"+str(test["id"])
            TestDashboardURL = "https://www.runscope.com/radar/"+str(Bucket["key"])+"/"+str(test["id"])
            TestDetail = requests.get(TestDetailURL,headers=headers,params=params)
            TestDetailData = json.loads(TestDetail.text)
            TestData = TestDetailData["data"]
            steps = TestData["steps"]
            #stepscount=str(len(steps))
            print(test["id"])           
            stepscount=count_steps(steps)           
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
                     detail.append(TestDashboardURL)
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
                detail.append(TestDashboardURL)
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
        