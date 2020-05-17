# blog.py

The purpose of this repo is to serve as a practical sandbox environment for developing skills working with web
technologies. At present, it's fairly light on features, and there are a number of issues that should be addressed.
These will be added as GitHub issues, and will allow you to contribute to an open-source project you can host for
your own blog as a pseudo portfolio piece.

If you use it for your own site, add it to `sites.md` to show the world.

## Background

Due to the Coronavirus pandemic, I've seen many students and new grads receiving rescinded offers. In browsing
around, I've noticed a common characteristic: many of them don't have any open-source contributions displayed.
If they do, it's something they solely built, rather than collaborated on. 

This is the basis for my actual [website/blog](http://blog.bdhimes.com). It works _fine_, as is, but certainly 
could use a number of features added or other things tweaked. I welcome contributions to this. Have a feature request?
Create a GitHub issue, and start work on developing it. See an open issue nobody is working on that you feel you
can tackle? Make a comment, and start working on it.

## Architecture

This is built using an asyncio Flask alternative called Quart. If you're familiar with Flask, you're familiar with Quart.
If you're not familiar with Flask, I recommend checking out the [Getting Started Guide](https://flask.palletsprojects.com/en/1.1.x/quickstart/). 
The Quart guide is also quite good, but Flask is a more mature, more widely used/known project, so it'll be good to start there.

Beyond that, blog.py stores and retrieves its posts from DynamoDB, an AWS NoSQL database. You can use a Dockerized instance
of DynamoDB hosted locally, for testing. When you're ready to connect it to your own DynamoDB, make sure to set up
the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html). I recommend Version 2.x, as it seems
to work quite a bit better, more smoothly than Version 1.x. If you're comfortable and already using 1.x, it should be fine
to continue doing so, at least for the purposes of running blog.py.

The post's body are expected in standard Markdown format (like this README), with the additional support for MD tables and 
code color syntax.

Most of the code is type-hinted and docstringed. If it's not, it's probably pretty self-explanatory what it does, but 
you are welcome to add a docstring or some type-hinting to it.

## Usage

In order to run blog.py, you'll need to set at least three environmental variables:
  - TITLE
  - INTO
  - BLOGTABLE
    
Of these, `BLOGTABLE` is probably the most important, because it tells the db_conn.py utility which database table to 
connect to. `TITLE` is the name of your blog, and `INTRO` is a quick snippet that describes your blog.

So, for example, to run blog.py using the app server `hypercorn` bound to localhost port 8080,
 for a blog called "My Blog", a decription of  "Musings and Thoughts", and a blog name name of "my-blog", 
 you would simply run:
 
```shell script
TITLE="My Blog" INTRO="Musings and Thoughts" BLOGTABLE="my-blog" hypercorn -b 0.0.0.0:8080 blog:app
```

Of course, you probably won't want to type that out each time, nor should you. So, you'll want to contruct a service, 
or whatever Windows has. 

Your service file might look something like this:
```
[Unit]
Description=Hypercorn instance serving my blog.
After=network.target

[Service]
User=bdhimes
Group=www-data
WorkingDirectory=/home/bdhimes/myblog
Environment="PATH=/home/bdhimes/myblog/venv/bin"
Environment="BLOGTABLE=my-blog"
Environment='TITLE="My Blog"'
Environment='INTRO="Musings and Thoughts"'
ExecStart=/home/bdhimes/myblog/venv/bin/hypercorn --bind 0.0.0.0:8080 blog:app

[Install]
WantedBy=multi-user.target
```

## Conclusion

Fork this repo and open a Pull Request with your changes. I'll review your code, and give the most constructive
criticism of it that I can. This is not about making this project the very best thing in the world, but rather
about allowing contributions with a fairly low bar to have an actual impact, in being able to see them live, either
on my site or on yours.

I intend to devote as much time as I can this Summer to reviewing code and giving feedback for contributions to 
this repo. If you somehow got to this repo hoping for a basic blog template, this will work, but keep in mind there will
likely be breaking changes to it over the next few months.

If you have any questions, feel free to reach out to me.
