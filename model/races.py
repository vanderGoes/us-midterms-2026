# Race metadata. PVI: positive = D lean (Cook PVI, as listed on Wikipedia race tables; Sept-Oct 2026).
# inc: +1 D incumbent running, -1 R incumbent running, 0 open. chal: 'D' or 'I' (main anti-R candidate's label).
# Ratings: Cook / Sabato / IE, latest available (see methodology notes in output).
REG = {}
for s in "ME NH VT MA RI CT NY NJ PA DE MD".split(): REG[s] = "Northeast"
for s in "OH MI IN IL WI MN IA MO ND SD NE KS".split(): REG[s] = "Midwest"
for s in "VA WV KY TN NC SC GA FL AL MS LA AR OK TX".split(): REG[s] = "South"
for s in "MT ID WY CO NM AZ UT NV CA OR WA AK HI".split(): REG[s] = "West"

# state, pvi, holder, inc, D/challenger name, R name, chal label, cook, sabato, ie
SENATE = [
 ("AL",-15,"R",0,"Everett Wess","Barry Moore","D","Solid R","Safe R","Solid R"),
 ("AK",-6,"R",-1,"Mary Peltola","Dan Sullivan","D","Toss-up","Lean D","Toss-up"),
 ("AR",-15,"R",-1,"Hallie Shoffner","Tom Cotton","D","Solid R","Safe R","Solid R"),
 ("CO",6,"D",1,"John Hickenlooper","Mark Baisley","D","Solid D","Safe D","Solid D"),
 ("DE",8,"D",1,"Chris Coons","Michael Katz","D","Solid D","Safe D","Solid D"),
 ("FL",-5,"R",-1,"Angie Nixon","Ashley Moody","D","Solid R","Likely R","Solid R"),
 ("GA",-1,"D",1,"Jon Ossoff","Mike Collins","D","Likely D","Likely D","Lean D"),
 ("ID",-18,"R",-1,"Todd Achilles","Jim Risch","I","Solid R","Safe R","Solid R"),
 ("IL",6,"D",0,"Juliana Stratton","Don Tracy","D","Solid D","Safe D","Solid D"),
 ("IA",-6,"R",0,"Josh Turek","Ashley Hinson","D","Toss-up","Lean R","Tilt R"),
 ("KS",-8,"R",-1,"Adam Hamilton","Roger Marshall","D","Toss-up","Lean D","Likely R"),
 ("KY",-15,"R",0,"Charles Booker","Andy Barr","D","Solid R","Safe R","Solid R"),
 ("LA",-11,"R",0,"Jamie Davis","Julia Letlow","D","Solid R","Lean R","Solid R"),
 ("ME",4,"R",-1,"Troy Jackson","Susan Collins","D","Toss-up","Lean D","Toss-up"),
 ("MA",14,"D",1,"Ed Markey","John Deaton","D","Solid D","Safe D","Solid D"),
 ("MI",0,"D",0,"Abdul El-Sayed","Mike Rogers","D","Toss-up","Lean D","Tilt D"),
 ("MN",3,"D",0,"Peggy Flanagan","Michele Tafoya","D","Lean D","Likely D","Lean D"),
 ("MS",-11,"R",-1,"Scott Colom","Cindy Hyde-Smith","D","Likely R","Safe R","Solid R"),
 ("MT",-10,"R",0,"Seth Bodnar","Kurt Alme","I","Solid R","Safe R","Solid R"),
 ("NE",-10,"R",-1,"Dan Osborn","Pete Ricketts","I","Likely R","Likely R","Lean R"),
 ("NH",2,"D",0,"Chris Pappas","John E. Sununu","D","Lean D","Lean D","Toss-up"),
 ("NJ",4,"D",1,"Cory Booker","Justin Murphy","D","Solid D","Safe D","Solid D"),
 ("NM",4,"D",1,"Ben Ray Luján","Larry Marker","D","Solid D","Safe D","Solid D"),
 ("NC",-1,"R",0,"Roy Cooper","Michael Whatley","D","Likely D","Likely D","Lean D"),
 ("OH",-5,"R",-1,"Sherrod Brown","Jon Husted","D","Toss-up","Lean D","Toss-up"),
 ("OK",-17,"R",0,"N'Kiyla Jasmine Thomas","Kevin Hern","D","Solid R","Safe R","Solid R"),
 ("OR",8,"D",1,"Jeff Merkley","David Brock Smith","D","Solid D","Safe D","Solid D"),
 ("RI",8,"D",1,"Jack Reed","Raymond McKay","D","Solid D","Safe D","Solid D"),
 ("SC",-8,"R",-1,"Annie Andrews","Darline Graham","D","Lean R","Lean R","Likely R"),
 ("SD",-15,"R",-1,"Brian Bengs","Mike Rounds","I","Solid R","Safe R","Solid R"),
 ("TN",-14,"R",-1,"Marquita Bradshaw","Bill Hagerty","D","Solid R","Safe R","Solid R"),
 ("TX",-6,"R",0,"James Talarico","Ken Paxton","D","Toss-up","Lean D","Toss-up"),
 ("VA",3,"D",1,"Mark Warner","Bert Mizusawa","D","Solid D","Safe D","Solid D"),
 ("WV",-21,"R",-1,"Rachel Fetty Anderson","Shelley Moore Capito","D","Solid R","Safe R","Solid R"),
 ("WY",-23,"R",0,"James W. Byrd","Harriet Hageman","D","Solid R","Safe R","Solid R"),
]
SENATE_SPECIAL = {"FL", "OH"}   # Class 3 specials (Rubio, Vance seats)
SENATE_HOLDOVER = {"D": 32, "R": 31, "I": 2}   # 65 seats not up; I = Sanders (VT), King (ME), both caucus D

GOV = [
 ("AL",-15,"R",0,"Doug Jones","Tommy Tuberville","D","Solid R","Safe R","Solid R"),
 ("AK",-6,"R",0,"Jonathan Kreiss-Tomkins","Bernadette Wilson","D","Lean D","Likely D","Lean R"),
 ("AZ",-2,"D",1,"Katie Hobbs","Andy Biggs","D","Lean D","Likely D","Tilt D"),
 ("AR",-15,"R",-1,"Fredrick Love","Sarah Huckabee Sanders","D","Solid R","Safe R","Solid R"),
 ("CA",12,"D",0,"Xavier Becerra","Steve Hilton","D","Solid D","Safe D","Solid D"),
 ("CO",6,"D",0,"Phil Weiser","Victor Marx","D","Solid D","Safe D","Solid D"),
 ("CT",8,"D",1,"Ned Lamont","Ryan Fazio","D","Solid D","Safe D","Solid D"),
 ("FL",-5,"R",0,"David Jolly","Byron Donalds","D","Likely R","Lean R","Likely R"),
 ("GA",-1,"R",0,"Keisha Lance Bottoms","Rick Jackson","D","Toss-up","Lean D","Toss-up"),
 ("HI",13,"D",1,"Josh Green","Gary Cordery","D","Solid D","Safe D","Solid D"),
 ("ID",-18,"R",-1,"Terri Pickens","Brad Little","D","Solid R","Safe R","Solid R"),
 ("IL",6,"D",1,"JB Pritzker","Darren Bailey","D","Solid D","Safe D","Solid D"),
 ("IA",-6,"R",0,"Rob Sand","Zach Lahn","D","Lean D","Lean D","Tilt D"),
 ("KS",-8,"D",0,"Cindy Holscher","Ty Masterson","D","Lean R","Lean R","Tilt R"),
 ("ME",4,"D",0,"Hannah Pingree","Robert Charles","D","Solid D","Likely D","Likely D"),
 ("MD",15,"D",1,"Wes Moore","Dan Cox","D","Solid D","Safe D","Solid D"),
 ("MA",14,"D",1,"Maura Healey","Mike Minogue","D","Solid D","Safe D","Solid D"),
 ("MI",0,"D",0,"Jocelyn Benson","John James","D","Lean D","Lean D","Tilt D"),
 ("MN",3,"D",0,"Amy Klobuchar","Lisa Demuth","D","Solid D","Safe D","Likely D"),
 ("NE",-10,"R",-1,"Lynne Walz","Jim Pillen","D","Likely R","Likely R","Solid R"),
 ("NV",-1,"R",-1,"Aaron Ford","Joe Lombardo","D","Toss-up","Lean D","Tilt R"),
 ("NH",2,"R",-1,"Cinde Warmington","Kelly Ayotte","D","Likely R","Lean R","Solid R"),
 ("NM",4,"D",0,"Deb Haaland","Gregg Hull","D","Solid D","Safe D","Likely D"),
 ("NY",8,"D",1,"Kathy Hochul","Bruce Blakeman","D","Solid D","Safe D","Likely D"),
 ("OH",-5,"R",0,"Amy Acton","Vivek Ramaswamy","D","Toss-up","Lean D","Tilt R"),
 ("OK",-17,"R",0,"Cyndi Munson","Mike Mazzei","D","Likely R","Safe R","Solid R"),
 ("OR",8,"D",1,"Tina Kotek","Christine Drazan","D","Likely D","Lean D","Lean D"),
 ("PA",-1,"D",1,"Josh Shapiro","Stacy Garrity","D","Solid D","Safe D","Solid D"),
 ("RI",8,"D",0,"Helena Foulkes","Aaron Guckian","D","Solid D","Safe D","Solid D"),
 ("SC",-8,"R",0,"Jermaine Johnson","Alan Wilson","D","Solid R","Safe R","Solid R"),
 ("SD",-15,"R",-1,"Dan Ahlers","Larry Rhoden","D","Solid R","Safe R","Solid R"),
 ("TN",-14,"R",0,"Jerri Green","Marsha Blackburn","D","Solid R","Safe R","Solid R"),
 ("TX",-6,"R",-1,"Gina Hinojosa","Greg Abbott","D","Likely R","Lean R","Likely R"),
 ("VT",17,"R",-1,"Amanda Janoo","Phil Scott","D","Likely R","Lean R","Solid R"),
 ("WI",0,"D",0,"David Crowley","Tom Tiffany","D","Toss-up","Lean D","Toss-up"),
 ("WY",-23,"R",0,"Kenneth Casner","Eric Barlow","D","Solid R","Safe R","Solid R"),
]
GOV_HOLDOVER = {"D": 6, "R": 8, "I": 0}   # DE KY NJ NC VA WA (D); IN LA MS MO MT ND UT WV (R)

# Third-party aggregate (PollCheck, 2 Nov) used as a single pseudo-poll where we did not pull poll-level data.
PSEUDO = {  # race: (D share, R share)
 "G-TN": (31.9, 40.7), "G-SC": (38.9, 48.5), "G-AL": (40.3, 50.3), "G-NY": (53.1, 41.2),
 "G-CT": (53.4, 37.3), "G-SD": (36.8, 53.3), "G-ID": (29.2, 46.3), "G-CA": (57.2, 35.6),
 "G-PA": (56.8, 34.2), "G-MA": (55.6, 33.1), "G-RI": (52.0, 39.3), "G-IL": (58.1, 39.5),
}
# G-RI: PollCheck lists Foulkes +12.7 with a three-way field (independent Ken Block); we encode the listed margin only.

# ---------------- House ----------------
# Union of non-safe seats in Cook (23 Oct), Sabato (30 Oct), Inside Elections (15 Oct) and the 270toWin consensus (23 Oct).
# Ratings themselves updated 3 Nov: Cook changes of 30 Oct and Sabato's final ratings of 2 Nov (see overrides at the end of this file).
# district: (pvi, holder_label, inc_running(+1 D/-1 R/0 open), note)
HOUSE = {
 "AK-AL":(-6,"R",-1,""),"AL-02":(-7,"D",1,"new map"),"AZ-01":(-1,"R",0,""),"AZ-02":(-7,"R",-1,""),
 "AZ-06":(0,"R",-1,""),"AZ-08":(-8,"R",-1,""),"AR-02":(-8,"R",-1,""),"CA-06":(5,"I",0,"Kiley (I) vs Pan (D)"),
 "CA-13":(2,"D",1,""),"CA-21":(5,"D",1,""),"CA-22":(1,"R",-1,""),"CA-45":(3,"D",1,""),"CA-48":(2,"R",0,"Prop 50 map"),
 "CO-03":(-5,"R",-1,""),"CO-04":(-9,"R",-1,""),"CO-05":(-5,"R",-1,""),"CO-08":(0,"R",-1,""),
 "FL-04":(-5,"R",-1,""),"FL-07":(-5,"R",0,""),"FL-09":(-8,"D",1,"new map"),"FL-12":(-7,"R",-1,""),
 "FL-13":(-6,"R",-1,""),"FL-14":(-4,"D",1,"new map"),"FL-16":(-6,"R",0,""),"FL-22":(-4,"D",0,"new map"),
 "FL-25":(-3,"D",1,"new map"),"FL-27":(-6,"R",-1,""),"IN-01":(1,"D",1,""),"IN-05":(-8,"R",-1,""),
 "IA-01":(-4,"R",-1,""),"IA-02":(-4,"R",0,""),"IA-03":(-2,"R",-1,""),"KS-02":(-10,"R",-1,""),
 "KY-06":(-7,"R",0,""),"LA-05":(-15,"R",0,"PVI estimated (new map)"),"ME-02":(-4,"D",0,""),"MD-01":(-8,"R",-1,""),
 "MI-03":(4,"D",1,""),"MI-04":(-3,"R",-1,""),"MI-07":(0,"R",-1,""),"MI-08":(-1,"D",1,""),"MI-10":(-3,"R",0,""),
 "MN-01":(-6,"R",-1,""),"MN-02":(3,"D",0,""),"MO-02":(-6,"R",-1,""),"MT-01":(-5,"R",0,""),
 "NE-01":(-6,"R",-1,""),"NE-02":(3,"R",0,""),"NV-01":(2,"D",1,""),"NV-02":(-7,"R",0,""),"NV-03":(1,"D",1,""),
 "NV-04":(2,"D",1,""),"NH-01":(2,"D",0,""),"NH-02":(2,"D",1,""),"NJ-02":(-5,"R",-1,""),"NJ-07":(0,"R",-1,""),
 "NJ-09":(2,"D",1,""),"NM-02":(0,"D",1,""),"NY-01":(-4,"R",-1,""),"NY-03":(0,"D",1,""),"NY-04":(2,"D",1,""),
 "NY-17":(1,"R",-1,""),"NY-19":(1,"D",1,""),"NY-21":(-10,"R",0,""),"NC-01":(-5,"D",1,"new map"),
 "NC-03":(-6,"R",-1,""),"NC-09":(-8,"R",-1,""),"NC-11":(-5,"R",-1,""),"NC-13":(-8,"R",-1,""),
 "OH-01":(-1,"D",1,"new map"),"OH-07":(-5,"R",-1,""),"OH-09":(-5,"D",1,"new map"),"OH-10":(-4,"R",-1,""),
 "OH-13":(2,"D",1,""),"OH-15":(-5,"R",-1,""),"PA-01":(1,"R",-1,""),"PA-07":(-1,"R",-1,""),"PA-08":(-4,"R",-1,""),
 "PA-10":(-3,"R",-1,""),"SC-01":(-6,"R",0,""),"TX-09":(-9,"R",0,"new R-drawn seat"),"TX-15":(-7,"R",-1,""),
 "TX-23":(-7,"R",0,"vacant"),"TX-28":(-3,"D",1,"new map"),"TX-34":(-3,"D",1,"new map"),"TX-35":(-4,"D",0,"new map"),
 "VA-01":(-3,"R",-1,""),"VA-02":(0,"R",-1,""),"VA-05":(-6,"R",-1,""),"VA-07":(2,"D",1,""),"WA-03":(-2,"D",1,""),
 "WA-05":(-5,"R",-1,""),"WI-01":(-2,"R",-1,""),"WI-03":(-3,"R",-1,""),"WY-AL":(-23,"R",0,""),
}
R_ = lambda s: s.split()
COOK = {}
for d in R_("CA-13 CA-45 IN-01 MI-08 MN-02 NE-02 NH-01 NJ-09 NV-01 NV-03 NV-04 NY-03 NY-04 NY-19 OH-01 OH-13 TX-28 VA-07"): COOK[d]="Likely D"
for d in R_("AZ-01 AZ-06 CA-48 CO-08 FL-25 IA-01 IA-03 NC-11 NJ-07 NM-02 PA-07 PA-10 TX-34 VA-02 WA-03 WI-03"): COOK[d]="Lean D"
for d in R_("CA-22 FL-14 FL-22 IA-02 KY-06 MI-04 MI-07 MI-10 MT-01 NC-01 NY-17 OH-07 OH-09 PA-08 TX-15 TX-35 VA-01"): COOK[d]="Toss-up"
for d in R_("AK-AL AL-02 AZ-02 CO-04 CO-05 FL-13 FL-27 ME-02 MN-01 NV-02 NY-21 OH-10 OH-15 PA-01 SC-01 TX-23 WI-01"): COOK[d]="Lean R"
for d in R_("AR-02 CO-03 FL-07 FL-09 FL-16 IN-05 KS-02 MO-02 NC-03 NC-13 NE-01 TX-09 VA-05"): COOK[d]="Likely R"
SAB = {}
for d in R_("CA-06 CA-13 CA-21 CA-45 CA-48 IN-01 MI-08 MN-02 NE-02 NH-01 NH-02 NJ-09 NV-01 NV-03 NV-04 NY-04 NY-19 OH-01 OH-13"): SAB[d]="Likely D"
for d in R_("AZ-01 AZ-06 CA-22 CO-08 FL-25 IA-01 IA-02 IA-03 NC-01 NC-11 NJ-07 NM-02 NY-03 PA-07 PA-08 PA-10 TX-15 TX-28 TX-34 VA-02 WA-03 WI-03"): SAB[d]="Lean D"
for d in R_("AL-02 CO-05 FL-14 FL-22 KY-06 MI-04 MI-07 MI-10 MO-02 MT-01 NY-17 OH-07 OH-09 PA-01 TX-35 VA-01 VA-05"): SAB[d]="Toss-up"
for d in R_("AK-AL AZ-02 CO-04 FL-13 FL-27 ME-02 MN-01 NV-02 NY-21 OH-10 OH-15 SC-01 TX-23 WI-01"): SAB[d]="Lean R"
for d in R_("AR-02 CO-03 FL-07 FL-09 FL-12 FL-16 IN-05 KS-02 LA-05 MD-01 NC-03 NE-01 NJ-02 NY-01 TX-09 WA-05"): SAB[d]="Likely R"
IE = {}
for d in R_("CA-45 IN-01 MI-03 MN-02 NH-02 NV-04 VA-07"): IE[d]="Likely D"
for d in R_("CA-06 NE-02 NH-01 NV-01 NV-03 NY-03"): IE[d]="Lean D"
for d in R_("AZ-01 CA-13 CA-48 IA-01 IA-03 NJ-07 NM-02 NY-04 OH-01 PA-07 PA-08 TX-28"): IE[d]="Tilt D"
for d in R_("AZ-06 CA-22 CO-08 FL-14 FL-25 IA-02 MI-07 NC-01 NC-11 NY-17 OH-07 OH-09 PA-10 TX-15 TX-34 VA-02 WA-03 WI-03"): IE[d]="Toss-up"
for d in R_("CO-05 FL-22 KY-06 MI-04 MI-10 MT-01"): IE[d]="Tilt R"
for d in R_("AL-02 FL-13 FL-27 ME-02 MN-01 NV-02 NY-21 PA-01 SC-01 TX-35 VA-01"): IE[d]="Lean R"
for d in R_("AK-AL AR-02 AZ-02 CO-03 FL-07 FL-09 FL-16 IN-05 NE-01 OH-15 TX-09 TX-23 VA-05 WI-01 WY-AL"): IE[d]="Likely R"
CONS = {}
for d in R_("AZ-06 CA-06 CA-13 CA-45 CA-48 IN-01 MI-08 MN-02 NE-02 NH-01 NH-02 NJ-09 NM-02 NV-01 NV-03 NV-04 NY-03 NY-04 NY-19 OH-01 OH-13 TX-28 VA-07"): CONS[d]="Likely D"
for d in R_("AZ-01 CA-22 CO-08 FL-25 IA-01 IA-03 NJ-07 PA-07 PA-10 TX-34 VA-02 WA-03 WI-03"): CONS[d]="Lean D"
for d in R_("FL-14 FL-22 IA-02 KY-06 ME-02 MI-04 MI-07 MI-10 MT-01 NC-01 NC-11 NY-17 OH-07 OH-09 PA-01 PA-08 TX-15 TX-35 VA-01"): CONS[d]="Toss-up"
for d in R_("AL-02 AZ-02 CO-03 CO-05 FL-07 FL-13 FL-27 MN-01 NV-02 OH-15 SC-01 TX-23 VA-05 WI-01"): CONS[d]="Lean R"
for d in R_("AK-AL AR-02 AZ-08 CO-04 FL-04 FL-09 FL-16 IN-05 KS-02 MO-02 NC-03 NC-09 NC-13 NE-01 NJ-02 NY-01 NY-21 OH-10 TX-09 WA-05"): CONS[d]="Likely R"
# Seats outside the union, rated Safe by every forecaster. 270toWin consensus (23 Oct): 220 D-favoured / 19 toss-up / 196 R-favoured.
CONS_SAFE_D, CONS_SAFE_R = 220 - 36, 196 - 34

# ---- Rating updates applied 3 Nov 2026 (Cook changes of 30 Oct; Sabato final ratings of 2 Nov)
for d, r in {"CO-05": "Toss-up", "OH-09": "Lean D", "PA-01": "Toss-up"}.items(): COOK[d] = r
for d in R_("AL-02 CO-05 FL-14 FL-22 MI-04 MI-07 MI-10 MT-01 OH-07 OH-09 PA-01 TX-35 VA-01 VA-05"): SAB[d] = "Lean D"
for d in R_("KY-06 MO-02 NY-17"): SAB[d] = "Lean R"
