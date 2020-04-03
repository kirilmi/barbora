## barbora.lt bot for getting available delivery times

To use this script - simply edit variable in dockerfile and build it:

```sh
docker build -t barbora .
```

To test it - run it:

```sh
docker run barbora
```

Finally, just add it as crontab:

```sh
* * * * * docker run --rm barbora
```