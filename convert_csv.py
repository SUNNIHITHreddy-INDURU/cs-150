import csv

input_file = "data/facebook_combined.txt"
follows_file = "data/follows.csv"
users_file = "data/users.csv"

users = set()
relationships = []

with open(input_file, "r") as file:
    for line in file:
        source, target = line.strip().split()

        users.add(int(source))
        users.add(int(target))

        relationships.append((source, target))

        relationships.append((target, source))

with open(follows_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["source", "target"])
    writer.writerows(relationships)

with open(users_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["userId", "username", "name", "email", "password", "bio"])

    for user_id in sorted(users):
        writer.writerow([
            user_id,
            f"user{user_id}",
            f"User {user_id}",
            f"user{user_id}@email.com",
            "123456",
            f"Bio for user {user_id}"
        ])

print(f"Total users: {len(users)}")
print(f"Total relationships: {len(relationships)}")