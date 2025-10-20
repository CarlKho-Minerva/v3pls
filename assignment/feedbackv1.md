Okay, this is a part of the two-pronged training process. And I guess the point of this message is to just make sure you update all the markdown files and make sure you have an actual narrative going on. Because what I see here are just a bunch of markdown files. Why don't we, at first, for section 1 to section 10 markdowns in the assignment folder, Why don't we convert all of them into IPYNB so we can have a data-driven narrative? In fact, that's what Professor Watson fucking preferred. So, let's go back and check. Did I not copy paste the Watson preferred checklist? There we are. We have the Watson preferred checklist. because he actually went over then did a live grading in class so that he could guide us with the we're about to output with that said yeah so first of all convert each and every section into an individual ipynbs and then create a merged ipynb with the complete cohesive narrative i like how you did the latex keep that but also reinforce that with the actual mathematics and be generous with the graphs and data visualizations because this is i say two-part process because there is a specific checklist here that check data point whatever that prof wants which is document choices made and rejected approaches which i'll give you in the second prop so keep that in mind make a markdown while specifically mentioning this in Karl's second part and ask for the data because I'll be giving it a lot. For now, though, because I don't want to contaminate the core principles, you're going to be working with this repository that I've isolated exclusively for the simple deceptively simple SVM. and now what I'm going to be doing is I'm going to be going through the explanations one by one or at least the I'm going to be going through each of the sections so I can give you my feedback and what to change so first off roundtable what I prefer is a markdown what I prefer is a markdown of your roundtable specific experts and of course Prof Watson himself you can personify him via Watson preferred markdown and the Watson preferred checklist and the writing tone is actually a bit of Ruff Watson himself so I want you to be more humble and be more straightforward but also keep it a tad bit entertaining without crossing boundaries because you talk like you were mansplaining with the writing tone but I did like the references of how like the historical references because it showed that I actually studied and looked And I guess the only thing missing from that are specific citations. So you have the internet, use that. So first data explanation. Gesture recognition data. Yeah, I guess the first part is like, yeah, I chose to actually execute physical actions for the sake of gestures. And it took a lot of studying because I did not know what IMUs were. and i initially used voice commands to approach it that's perfect yep i know this because i tried to avoid it it's perfect and i really like i did what any reasonable ml practitioner keep this ton of voice it keeps them on their toes but for the data collection architecture yes i guess we could say yeah uh you could even no this is for part two so annotate this but in part two even mentioned that we started off with emgs classifying emgs clenched or not clenched so because i couldn't satisfy that i thought i should make something complicated which is a rookie mistake given that i only had a few days for assignment anyway data collection architecture yep pixel watch i would say make a correction for this data diagram for pixel watch left wrist and android phone right hand it looks intuitive yeah you know what let's just keep that linear process there look everything looks good and why it's hard Yep. Yep. I like why this matters data structure makes sense. Well, sample counts. This is the most important part. Every one of the classes now have 120 samples each. If you don't trust me, check out the data. the data column everything except walk which we can obviously which i didn't really focus because the binary classifier was performing well and then i just needed more idle steps so that my multi-classifier which has this chopped up idle to match the duration I want I have that there and yeah so that's why I only added 120 samples anyway dual classifier yeah I learned from version one of my silk song from capstone which I will not refer but the point is i realized the power of multi-threading and then of course locomotion states past four year stuff everything looks good this is not a common approach then check for discrete actions combined prediction hierarchically actually for this one it makes me it helps if this is raw i want to do them in parallel so because silk song inherently and by the way silk songs out it's already october 2020 25 people have completed the game but silk song is a fast-paced game so that's why i want it to be parallel because i want actions i still want to walk but i also want actions to happen because i can jump and walk and also just be idle and walk and that's the my uh udb listener dashboard although it's using async io it's not really working well maybe and the image asks because for figures here add some figures please let me know which figures to add like add set make so for every section i expect a roundtable markdown the actual ipynb for section and then a markdown or even within the ipynb just a markdown asking for what photos to add, how to take them, where I can find them, or even set up the code in advance. So that's my feedback for section 1 data explanation, not the clean version. Back to the assignment, we've got data 2, loading, file naming convention. Yeah, I like this point. More robust than column-based labels. I never even thought of that. But yeah, it also preserves honesty for me. And oh, we need to add a point about data ethics. Specifically answer this question. Because Prof emphasized, like adding, ethical for ethical data ethics we have to be where was that last question there was this question that properly emphasized that what ethical considerations might you use and this was my answer ethics and this is what I responded with but I guess the ethics here is that I responded that okay I'm only using my bound by signals but in the future maybe other biometric identifies with compromised privacy but since we're not there emphasize that I've used this that I've used this file naming specifically. Oh, but it's a Unix time in milliseconds. It's not even telling me when. But anyway, point is I've tried to be more transparent by using this type of file naming and not modifying the metadata. Copy core data loading function. I do not know what this core data loading function is because the workflow I go through and reference Python files. I want you to actually reference the Python files or add them into the notebook itself because the workflow I go through is, of course, I get the data. I use merge sensor rows and then on merge sensor rows output folder, I use the organized training data dot py to group them. Okay. Why? Okay. These design decisions are tiny, but these are considered. I like it because you are being very considerate. Okay. Yeah, I guess you have to mention that. Yeah, for reading the CSV format, you actually skip the narrative here. And that's that my sensors sense separate rows of data. So you might see a bunch of zeros in them. looking through an example data like dissect the specific data point let's do one punch that's the single punch here dissect the singular punch yeah cool and now let's move on to section three feature engineering yep oh you talked about this here by combining both we capture complementary yeah this is not it's a standard when you mention bullying et al and lara and labrador can you cite specific parts of the paper but it's not obvious if you've only done image classification is kind of condescending so maybe frame it more of like but i learned that extract features and from data frame cool this looks good let me justify each category love the latex here if you could add some math that would be great why not deep learning features of course i have 120 on me and i've already lost perhaps i've lost a few pounds from that data cleaning yep this is this is uh considerate i like this no explicit noise exploratory data exploratory data again valuable if you can actually code this and plot this the image is required for notebook cool but i want you to embed this inside the notebook itself and i like the references for section three put them in ipy and v that's my feedback so far analysis discussion and data splits. Supervised classifications. Huh, I think you're getting out of touch here. Like section 4 corrections. Update this in the actual IPYNB. Background context for wearable applications. what are you doing specifically mention silksong relevant applications like hollow knight specific because i wanted a binary classification to be very clear that it's a walk given that the amplitude and it's just a different function because it's a five second clip to capture the entire sine wave or something and then multi-class is to just because they're like short and sweet we've talked about this in section one can you just make it cohesive and uh what do you call it cohesive and uh relevant and you know like specific which brings me to my next point or current section one to ten I really like them put in archive don't delete and then make the new stuff I tell you which is the 1md of round table the ipynb itself and then a markdown of images but again it's preferred if you put the images or figures inside the type of YNB. Okay now why not clustering? Why supervise classifications? Why to classify instead of one? Yeah okay cool you've already talked about that. Okay cool. Okay cool. so here's the pitfall leaky temporal data consider the three samples okay if you actually consider that can you then use pandas to specify which specific portions you want to feature data collection spanned multiple days even multiple sessions now yeah these were not collected consecutively this temporal autocorrelation yep implementation stratified split random state 42 let's change this 6-7 because of as a marker of the recent meme important and transparent case for transparency. Let the XP hour. Okay, I'll leave you with the math. But then again, I want this to be actually correct math. So do the latex and then do the code below it and then go to markdown. Do the markdown explanation. Why not cross validation? Although we talked about this in class. Yeah, easier to explain and implement. So when you say it's easier to explain. Okay, so you've already explained that. I thought you didn't explain. Cool. 4 looks good. Module selection time. Discussion of module selection and markdown. Dissections should include a clear discussion of the module's mathematical underpinnings. Okay, mathematical underpinnings. We could use a lot of StatQuest videos here. I assume you could query the internet and get that. Say that StatQuest was my main reason or something. I'm still recording right? Okay cool. okay cool these look cool it would be nice to have if we actually ran individual modules like ysvm why not knn why not decision trees it will be cool to run them and compare and have a table at the end and say that svm emerged victorious but we'll never know maybe svm won't emerge victorious some of these are redundant i think there was another section that talked about different models so let's just do the hyperplane equation so i remember stat was giving out a lot of very good visualizations planes um 1d lines so if you could replicate that here using seaborn or matplotlib for each equation that would be very good the goal here is to show that i understood so when you explain svms you can have the general explanation and then what this means for my project is you know you personalize the mathematical explanation and i like the soft margin formulation the kernel trick yeah that looks good kind of looks ai though when you use uh the kernel trick colon maybe reduce colon usage across using the tailor expansion whoa whoa whoa for this one yeah I think it would be a stretch proof sketch do we really need a proof though uh should I do you want oh this is important well if you want me to well for proof sketch of the tailor yes you can run it but also I can do a handwritten paper stuff if we want it to look more legit then I can insert the image here let me know what you want and let me know what to write because I don't know what infinite dimensional is only points with okay decision function with RBF support vectors sports and efficient multi-class extensions OVO one versus one binary Oh, okay. SVMs are inherently binary classifiers. Damn, that's interesting. Example for a multi class classifier. I want a notebook here. I would sell here please section five or above. to prove this data model implementation sure that looks that works why standard scalar i thought euclidean distance doesn't work critical implementation detail fit on all data data leakage never do this this is this feels more like an sop instead of like i didn't do this i made sure you know instead of maybe we could even fit this rephrase too i made a mistake doing this initially hyperparameter choices default on a scalar increase to reduce underfitting quo gamma auto wow very very very very considerate and you even have the quadratic problem yeah i guess for these for the smo algorithm and the kkt conditions please please link them and please explain how I got to find them in the first place maybe so I got into a rabbit hole god damn okay cool computational complexity thank you now let's go to model training so section six training application you know prof wanted a from scratch application but I don't think that would be realistic here no? Yep and then here what happens inside svm fit make sure you gather multiple sources and say that it took me a bunch of reading to actually understand this. And then because we know that the implementation from statquest and scikit learn is different so I had to read. Quadratic programming, support factor identification, okay sanity check, training accuracy. Oh okay my results i think who i think we did worse but hey point is we learned and in actuality the data does differentiate like again the only problem is the data differentiates it's just that i have haven't engineered a way to queue things up yet but if you look at the data i've even implemented debouncing it accurately detects a punch versus a turn versus noise and idle it doesn't expose convergence metrics i don't know what this is but please document well via markdown and code cells hyperparameters true name Okay, save models for the plan Okay, performance metrics yep this is pretty good accuracy i can i like the general explanation here but then contextualize it really point back to data precision default yep and then code cells please yep and I assume this is updated be sure to update these confusion matrix yep if you can please actually view image or code underlying to dissect confidence analysis per class error analysis okay code self that goes to code self always compare to simple place baselines always compare to simple baselines should we train a different model for our baseline. I think I need help here and statistical significance. Okay yeah you can do that and then results, conclusions, visualize, okay I'll do that. Visualization 2 feature importance analysis which features drive the decision boundary. I really like it because it's explainable and then references cool the only ask I have is can you actually embed the references I think we're using a api citation so I guess you can just do like I found this by stat quest draw stream or 2020 something whatever well there's that




"/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_1_data_explanation_clean.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_1_data_explanation.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_2_data_loading.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_3_feature_engineering.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_4_analysis_splits.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_5_model_selection.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_6_model_training.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_7_performance_metrics.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_8_results_conclusions.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_9_executive_summary.md
/Users/cvk/Downloads/CODELocalProjects/v3pls/assignment/section_10_references.md

120 SAMPLES!
{
  "idle": 120,
  "turn_left": 120,
  "turn_right": 120,
  "noise": 120,
  "jump": 120,
  "walk": 71,
  "punch": 120
}
/Users/cvk/Downloads/CODELocalProjects/v3pls/data/organized_training/metadata.json



WRONG
"Combine predictions hierarchically: first determine locomotion state, then check for discrete actions"

What ethical considerations are critical for the data set you chose for assignment 1? For example, are their privacy or consent concerns? How
will the insights you create be used?
Your Answers:
Carl Vincent Kho
Since n=1 →. my own biosignals locally processed, none so far. However, if I scale this up others' biometric identifiers could compromise
privacy by using such data to identify identities, reveal health conditions → black mail material?

WHAT? Core Data Loading Function be clearer and reference python files /Users/cvk/Downloads/CODELocalProjects/v3pls/src/merge_sensor_rows.py -> /Users/cvk/Downloads/CODELocalProjects/v3pls/src/organize_training_data.py


Where merge? Reading the CSV Format
Each CSV file contains 50Hz IMU data:

DISSECT HTIS /Users/cvk/Downloads/CODELocalProjects/v3pls/data/button_collected/punch_1760926656847_to_1760926657657.csv


This is not novel—it's standard practice from Bulling et al. (2014) and Lara & Labrador (2013). But it's non-obvious if you've only done image classification.



SECTION 4 CORRECTIONS
ask 1: Binary Classification (Locomotion State)

Classes: Walk, Idle
Goal: Determine if the user is moving or stationary
Use case: Background context for wearable applications (e.g., "don't show navigation alerts while user is sitting")
Task 2: Multiclass Classification (Discrete Gestures)

Classes: Jump, Punch, Turn Left, Turn Right, Idle, Noise
Goal: Recognize specific intentional gestures
Use case: Gesture-based UI control (e.g., punch to confirm, turn to navigate menu)

FOR CURRENT SECTION 1 - 10 -> PUT IN ARCHIVE, DONT DELETE, AND THEN MAKE THE NEW STUFF


The Pitfall: Leaky Temporal Data
Here's a subtle mistake I avoided. Consider this dataset:

walk_1760841757694_to_1760841762941.csv  (Sample 1)
walk_1760841765000_to_1760841770000.csv  (Sample 2)
walk_1760841772000_to_1760841777000.csv  (Sample 3)
These three samples were collected sequentially within 20 seconds. They're not truly independent:


random_state=42 (reproducibility) -> 67 as a marker of 2025 meme landscape



CODE CELL HERE PLS SECTION 5 FOR ABOVE TO PROVE THIS WITH DATA:
"
Example for multiclass classifier:

SVM(jump vs. punch) predicts: punch
SVM(jump vs. turn_left) predicts: jump
SVM(punch vs. turn_left) predicts: punch
... (12 more comparisons)
Final vote count: punch (7 votes), jump (5 votes), turn_left (3 votes)
Prediction: punch"


Rephrase to "I made the mistake of doing this initially: # WRONG: Fit on all data (data leakage!)
scaler.fit(np.vstack([X_train, X_test]))  # ❌ NEVER DO THIS"



SECTION 6

PROOF? My results:

Binary classifier: 98.2% training accuracy
Multiclass classifier: 94.4% training accuracy
 I THINK WE DID WORSE


SECTION 7
 BE SURE TO UPDATE THESE

Punch/Turn_right: Lowest performance (83.3% F1) — likely confusable with other ballistic motions

PLEASE ACTUALLY VIEW IMAGE OR CODE UNDERLYING TO DISSECT
Multiclass confusion matrix (actual):

                Predicted
          jump punch tl   tr  idle noise
True jump   11    0   0    1    0    0
     punch   0   10   0    0    2    0
     tl      0    0  11    0    1    0
     tr      1    0   0   10    1    0
     idle    0    0   0    0   11    1
     noise   0    0   0    1    0   23


     Comparison to Baselines
Always compare to simple baselines to validate your model isn't doing something trivial:



SHOULD WE TRAIN A DIFF MODEL FOR THIS?!?!

"