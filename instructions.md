Individual Assignment: An Architecture Reconstruction Project 


Goal 
The report should present the architecture reconstruction results of an open source system. A list of possible systems is proposed below. If you want to analyze another system you should have a good reason for it and confirm with a member of the staff that your system qualifies. 
The goal of the project is to recover one or more architectural views and to present them in a brief report. The audience of the report is somebody who has not seen that system before and needs to get a high-level understanding of the system.
Your report should show that you have developed a good understanding of the system, and show which techniques from architecture reconstruction you have used. 
If you used off-the-shelf tools or you implemented your own scripts, discuss the tools and the way they helped you. If you spent time implementing an advanced analysis tool, make sure to describe that. The analysis part of your report can be less extensive in this case. 
You choose which architecturally relevant viewpoints you want to include in your report.
A module view is the simplest, and this is also why we focused the first two AR lectures on it. However, make sure to explain it well by describing the roles of both the modules and the dependencies in it (remember the discussion about “verbs and nouns” in Lecture 11). 
As a more advanced case of a module view you can decide to extract a reflexion model. Ask one of the developers of your system for a hypothetical view; or find one in the documentation. Then see whether the system conforms to it.
You get extra bonus for making sure that the visualization is clear and expressive. A Polymetric viewpoint would be excellent. 
Other viewpoints could also make sense:
You could recover a deployment view or a component and connector view if you have access to deployment files (e.g., docker-compose.yml, Dockerfile, etc.).


Possible subject systems 
The Zeeguu-API: Python backend.
The Zeeguu-React: React frontend
A combination of the previous two that finds a way to automatically extract dependencies between backend and frontend
A system of your choice of comparable size (i.e. approx 10K LOC)
Possible focus & time allocations
Effort should be proportional to 4 days of fulltime work. However, the way you spend that time should be directed by your interest and your capabilities (e.g. you can decide to spend more of the time building similar analysis scripts or modifying the analysis scripts that we created in the classroom; or more of the time doing the analysis; or even reading code)
20% tool finding & comparison - 40% analysis - 40% writing
60% script building - 10% analysis - 30% writing (for those who are more interested in script-building)
Structure of the Report
Write this report as it were written for a fellow architect who took this course. You don’t have to explain concepts and spend time on references. Present the results of your recovery process, and explain what you did and why you did it. 
Also, try to keep it short. As a rule of thumb, you should not need more than 3-4 pages for the individual report part. If you really have more content, then keep the essential in the main body, and move the less essential parts to an appendix. 

Introduction 
What is the problem?
What is the system? 
Methodology
Tool support: did you use any off-the shelf tools? Your own scripts? Adapt the ones in the course?
Data gathering: what sources of data did you use? Source viewpoints? Reverse engineering patterns? 
Knowledge inference: did you use any abstraction approach? What target viewpoint do you want to recover? 
Results 
The most relevant architectural views (one to three at most) that you recovered from the analysis of the system
Explain the elements in the architectural view(s)
Discussion 
​​[optional] Recommendations for reengineering of the system (did you discover things that seem wrong and should be corrected?)
What are the limitations of your approach 
What would you do better if you had more time
Appendix 
Brief description of your code and link to GH repository or Collab notebook
Time allocation: how did you spend your time
Deadline 
Submit by the deadline in LearnIt.Then you have one week to review each other’s reports.
