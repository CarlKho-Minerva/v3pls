0:00 I'm gonna start by saying I have so much respect for a manual data labelers. I try to get around it with the whole, Use my voice as I walk thing, because I'm just expecting, A bunch of late nights.
0:27 I still couldn't get my model passed 30%. There was a bunch of sinking issues, and there were also a bunch of time stamp issues.
0:38 And so what I did is, with the help of an advice from a very good friend, I have adapted this.
0:48 Button-based data logging with automatic labeling, and it tells me how many samples I've had here. I've also connected it to my watch.
0:57 So in a sense, I have not been able to escape Phase 2, which is data collection with the smartphone watch.
1:04 It did eventually happen after I've been trying to go around it because it's like, oh, it's the same thing as my initial threshold approach.
1:12 Anyway. We'll see enough about that. Two good things about this. Oh, three good things about this. Number one. Very, very rich real time.
1:21 Fresh data. I am in awe with this data collection dashboard. It is very clean. So instead of having the walk as the default data label, we're having noise.
1:33 And I guess what I was trying to get rid of Riddle with this approach is the over-dominance of a specific data category.
1:43 Because I think walk had like 5k samples and so it took up 70% of training data. And so the confusion matrix would always just show almost all of the predictions being made towards walk.
1:56 So I went around that. And so for noise, I have uhh, uhh, uhh, approximate that a sample size of 30, although I've gone ahead and did 40 for safety.
2:07 So there's like 30 samples of noise in the beginning where I scratched my head and did everything. Now I tried to click buttons on the keyboard as if to emulate the settings change.
2:19 Anyway, how this works is it first gets both our streaming UDP. This one's streaming the sensor data. And this is exclusively labeling with specific timestamps.
2:30 And we can see the phone app having a lower rate because it doesn't really need that much. And now, now that they're both ready, only then will this dashboard activate where in this dashboard there are years to latest sensor data.
2:46 And so it's switching between rotations. . And the sensor, gyroscope, and linear accelerator. And it shows you how fresh the data is, the way it's specific timestamps.
2:56 I fixed this already. And now we have acceleration without the gravity, gyroscope and radiance, and the rotation factor in core turnyons.
3:04 And so far we've had a total recording of 225. What do you mean? Anyway. This, if you notice there is some slight mismatch, because I love a dogless system.
3:18 This it also allows me to immediately delete ugly data. So data where I feel like I, for example, I say punch, but I've actually punched it twice.
3:30 Which is not a good thing. So now I can just look at the, sorry, file sizes, quite unconventional. I could get rid of a bigger than average punch.
3:41 Which I can't see right now, but hey, it's a punch. And when I walk, and then I guess the second approach that I took here is that the walk and the idle, they're trained on their own models.
3:51 It's a binary classifier. Because I think it's gonna be hard given that walks and idle typically consume more time stamps.
4:01 When you're training them for specificity, I'm doing a five second walk interval and five second idle interval, while everything else is within the range of four, two seconds.
4:11 So, in other words, a binary classifier for walk or not walk. And a multi-classifier, which is just a four action, so on.
4:19 Turn left, turn right. I was specified now. A punch on a jump. And, I'm going back to- That's because if I see, like, if I accidentally encounter, um, bug or, like, holds indefinitely, because it activates by holding.
4:37 When it holds indefinitely, I can just go here and delete it. Which is why it says I have 38 turns R's.
4:42 But I actually have 40 over here. The two were just deleted. And- Of course, I get to keep the organic side.
4:51 Okay, I'm gonna go ahead and do some training like this, but I'm like, okay, walk. So, it's still pretty organic.
5:02 Let's hope for the ass to be on. Or, uh, explain it last year on this. And I'm really excited because I just can't access the Colhab Pro, which means I get the last few hundreds.
