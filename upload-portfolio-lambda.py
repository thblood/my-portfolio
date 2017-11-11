import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:156237913651:deployPortfolioTopic')

    location = {
        "bucketName": 'portfoliobuild.charter.city',
        "objectKey": 'portfoliobuild.zip'
    }

    try:
        job = event.get("CodePipeline.job")
        print "Trying job now ..."
        if job:
            print "Starting job loop now ..."
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "myAppBuild":
                    location == artifact["location"]["s3Location"]

        print "Building portfolio from" + str(location)
        s3 = boto3.resource('s3')
        portfolio_bucket = s3.Bucket('portfolio.charter.city')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print "Job Done!"

        topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed successfully!")
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="Portfolio Deploy Failed", Message="Portfoilio was not deployed successfully!")
        raise

    return 'Hello from Lambda'
