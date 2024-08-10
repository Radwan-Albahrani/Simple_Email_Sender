import json

# open responses.json and parse the data
with open("input/response.json") as json_file, open("output/emails.json", "w") as f:
    data = json.load(json_file)
    email_list = []
    for p in data["data"]["response"]["exhibitors"]["nodes"]:
        if p.get("email"):
            result = {"name": p["name"], "emails": p["email"].split(",")}
            if len(result["emails"]) > 1:
                result["emails"] = [email.strip() for email in result["emails"]]
            email_list.append(result)
    json.dump(email_list, f, indent=2)

with open("input/response_startups.json") as json_file:
    data = json.load(json_file)
    email_list = []
    for p in data["data"]["response"]["exhibitors"]["nodes"]:
        if p.get("email"):
            result = {"name": p["name"], "emails": p["email"].split(",")}
            if len(result["emails"]) > 1:
                result["emails"] = [email.strip() for email in result["emails"]]
            email_list.append(result)

    with open("output/emails_startups.json", "w") as f:
        json.dump(email_list, f, indent=2)

    with open("output/emails.json", "r") as f:
        data = json.load(f)
        data.extend(email_list)

    with open("output/emails.json", "w") as f:
        json.dump(data, f, indent=2)


# clean any duplicates
objects_seen = set()
with open("output/emails.json", "r") as inFile:
    data = json.load(inFile)
    cleaned_data = []
    for obj in data:
        if obj["name"] not in objects_seen:
            cleaned_data.append(obj)
            objects_seen.add(obj["name"])
        else:
            print(f"Duplicate: {obj['name']}")
    with open("output/emails_cleaned.json", "w") as outfile:
        json.dump(cleaned_data, outfile, indent=2)

# Keep only Latin Characters in the name
import re

with open("output/emails_cleaned.json", "r") as inFile:
    data = json.load(inFile)
    cleaned_data = []
    for obj in data:
        obj["name"] = re.sub(r"[^\x00-\x7F]+", "", obj["name"])
        for index, email in enumerate(obj["emails"]):
            email = re.sub(r"[^\w\.-@]", "", email)
            obj["emails"][index] = email
        obj["name"] = re.sub(r"[^A-Za-z0-9\s]+", "", obj["name"])
        obj["name"] = obj["name"].strip()
        cleaned_data.append(obj)
    with open("output/emails_cleaned.json", "w") as outfile:
        json.dump(cleaned_data, outfile, indent=2)

with open("output/emails_startups_cleaned.json", "r") as inFile:
    data = json.load(inFile)
    cleaned_data = []
    for obj in data:
        obj["name"] = re.sub(r"[^\x00-\x7F]+", "", obj["name"])
        for index, email in enumerate(obj["emails"]):
            email = re.sub(r"[^\w\.-@]", "", email)
            obj["emails"][index] = email
        obj["name"] = re.sub(r"[^A-Za-z0-9\s]+", "", obj["name"])
        obj["name"] = obj["name"].strip()
        cleaned_data.append(obj)
    with open("output/emails_startups_cleaned.json", "w") as outfile:
        json.dump(cleaned_data, outfile, indent=2)
