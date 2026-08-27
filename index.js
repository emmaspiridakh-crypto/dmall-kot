const fs = require('fs');
const prefix = "!";
const path = require("path");

const {
    Client,
    GatewayIntentBits,
    Partials,
    Collection,
    EmbedBuilder,
    ContainerBuilder,
     PermissionsBitField,
       ChannelType,
    ActionRowBuilder,
    MediaGalleryItemBuilder,
    StringSelectMenuBuilder,
    ButtonBuilder, 
    ButtonStyle,
    PermissionFlagsBits,
    ModalBuilder,
    MessageFlags,
    Events,
    AuditLogEvent ,
    SectionBuilder,
    TextInputBuilder,
    InteractionType,
    TextInputStyle
} = require("discord.js");
const cron = require("node-cron");
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildPresences,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessageReactions,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildBans
  ],
  partials: [
    Partials.Message,
    Partials.Channel,
    Partials.Reaction,
    Partials.User,
    Partials.GuildMember
  ]
});


 

client.login("VALE TOKEN EDO");

const GUILD_ID = "1477021452686327880";

const TESTLOG_CHANNEL_ID = "1542589533734961193";

// User IDs που ΔΕΝ θα λάβουν DM
const EXCLUDED_USER_IDS = [
  ""
];

const delay = 1000;
const dbPath = "./dmdata.json";

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function loadData() {
  if (!fs.existsSync(dbPath)) {
    fs.writeFileSync(
      dbPath,
      JSON.stringify(
        {
          sent: [],
          message: ""
        },
        null,
        2
      )
    );
  }

  try {
    return JSON.parse(
      fs.readFileSync(dbPath, "utf8")
    );
  } catch (error) {
    console.error("❌ Error reading dmdata.json:", error);

    return {
      sent: [],
      message: ""
    };
  }
}

function saveData(data) {
  fs.writeFileSync(
    dbPath,
    JSON.stringify(data, null, 2)
  );
}

async function sendDMall(guild, messageContent, continueMode = false) {
  let data = loadData();

  // Νέο DM all
  if (!continueMode) {
    data = {
      sent: [],
      message: messageContent
    };

    saveData(data);
  }

  // Continue από το προηγούμενο DM all
  if (continueMode) {
    if (!data.message || data.message.trim() === "") {
      const logChannel = guild.channels.cache.get(
        TESTLOG_CHANNEL_ID
      );

      if (logChannel) {
        await logChannel.send(
          "❌ No saved message in DB."
        );
      }

      return;
    }

    messageContent = data.message;
  }

  const sentIds = data.sent;


  const members = await guild.members.fetch();

  const usersToDM = members
    .filter(member => {
      if (member.user.bot) return false;

      if (sentIds.includes(member.id)) {
        return false;
      }

      if (EXCLUDED_USER_IDS.includes(member.id)) {
        return false;
      }

      return true;
    })
    .sort((a, b) => {
      const aOnline =
        a.presence &&
        a.presence.status !== "offline";

      const bOnline =
        b.presence &&
        b.presence.status !== "offline";

      if (aOnline === bOnline) {
        return 0;
      }

      return aOnline ? -1 : 1;
    });

  const logChannel = guild.channels.cache.get(
    TESTLOG_CHANNEL_ID
  );

  if (!logChannel) {
    console.error("❌ Log channel not found!");
    return;
  }

  const total = usersToDM.size;

  let count = 0;
  let successCount = 0;
  let failedCount = 0;

  // Μετρητής συνεχόμενων failed DMs
  let consecutiveFailed = 0;
  let stoppedEarly = false;

  console.log(
    `📨 Starting DM all... ${total} users`
  );

  for (const [id, member] of usersToDM) {
    count++;

    try {
      await member.send(messageContent);

      successCount++;
      consecutiveFailed = 0;
      sentIds.push(member.id);

      saveData({
        sent: sentIds,
        message: messageContent
      });

      const progress = `${count}/${total}`;

      const logMsg =
        `${progress}. ✅ Sent DM to ${member.user.tag} (<@${member.id}>)`;

      await logChannel.send(logMsg);

      console.log(logMsg);

    } catch (err) {
      failedCount++;
      consecutiveFailed++;
      sentIds.push(member.id);

      saveData({
        sent: sentIds,
        message: messageContent
      });

      const progress = `${count}/${total}`;

      const logMsg =
        `${progress}. ❌ Couldn't send DM to ${member.user.tag} (<@${member.id}>) — DMs closed.`;

      await logChannel.send(logMsg);

      console.log(logMsg);
      if (consecutiveFailed >= 4) {
        stoppedEarly = true;

        const stopMessage =
          "🛑 **DM-all stopped because 4 consecutive DMs failed.**\n" +
          "Use `!continuedmall` to continue later.";

        await logChannel.send(stopMessage);
        console.log(stopMessage);

        break;
      }
    }

    await sleep(delay);
  }

  if (stoppedEarly) {
    await logChannel.send(
      `🛑 **DM-all stopped early!**\n` +
      `📨 Total processed: **${count}/${total}**\n` +
      `✅ Successfully sent: **${successCount}**\n` +
      `❌ Failed: **${failedCount}**\n` +
      `🚫 Excluded: **${EXCLUDED_USER_IDS.length}**`
    );

    console.log("DM-all stopped after 4 consecutive failures.");
    return;
  }

  // Τελικό log
  await logChannel.send(
    `✅ **DM-all completed!**\n` +
    `📨 Total processed: **${count}**\n` +
    `✅ Successfully sent: **${successCount}**\n` +
    `❌ Failed: **${failedCount}**\n` +
    `🚫 Excluded: **${EXCLUDED_USER_IDS.length}**`
  );

  console.log("DM-all completed!");
}


client.on("messageCreate", async message => {
  if (!message.content.startsWith("!")) return;
  if (message.author.bot) return;

  const args = message.content.split(" ");
  const command = args.shift().toLowerCase();

  const guild = message.guild;

  if (!guild) return;

  if (command === "!dmall") {

    if (
      !message.member.permissions.has(
        PermissionsBitField.Flags.Administrator
      )
    ) {
      return message.reply("❌ No perms.");
    }

    const content = args.join(" ").trim();

    if (!content) {
      return message.reply(
        "❌ Use `!dmall <message>`."
      );
    }

    await message.reply(
      "📨 Sending DM to all users..."
    );

    sendDMall(
      guild,
      content,
      false
    ).catch(error => {
      console.error(
        "❌ DM-all error:",
        error
      );
    });

    return;
  }

  if (command === "!continuedmall") {

    if (
      !message.member.permissions.has(
        PermissionsBitField.Flags.Administrator
      )
    ) {
      return message.reply("❌ No perms.");
    }

    await message.reply(
      "📨 Continuing DM all..."
    );

    sendDMall(
      guild,
      null,
      true
    ).catch(error => {
      console.error(
        "❌ Continue DM-all error:",
        error
      );
    });

    return;
  }


  if (command === "!cleardmall") {

    if (
      !message.member.permissions.has(
        PermissionsBitField.Flags.Administrator
      )
    ) {
      return message.reply("❌ No perms.");
    }

    saveData({
      sent: [],
      message: ""
    });

    await message.reply(
      "✅ DM database cleared."
    );

    return;
  }
});


client.once("ready", () => {

  console.log(
    `✅ Logged in as ${client.user.tag}`
  );

  if (!fs.existsSync(dbPath)) {

    fs.writeFileSync(
      dbPath,
      JSON.stringify(
        {
          sent: [],
          message: ""
        },
        null,
        2
      )
    );

    console.log(
      "✅ dmdata.json created."
    );
  }

  console.log(
    `🚫 Excluded users: ${EXCLUDED_USER_IDS.length}`
  );
});