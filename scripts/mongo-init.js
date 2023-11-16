db = db.getSiblingDB("eden-bots-dev");

db.createUser({
  user: "eden",
  pwd: "eden",
  roles: [
    {
      role: "readWrite",
      db: "eden-bots-dev",
    },
  ],
});

db.createCollection("commands");

const commands = [
  {
    bot: "eden",
    commands: [
      {
        name: "test",
      },
    ],
  },
];

db.commands.insertMany(commands);
