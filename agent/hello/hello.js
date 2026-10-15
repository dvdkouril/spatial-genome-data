const name = process.env.GREETING_NAME ?? "world";

setInterval(() => {
  console.log(`hello ${name}, it's ${new Date().toISOString()}`);
}, 5000);
