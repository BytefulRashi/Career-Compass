from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    FileReadTool,
    EXASearchTool
)
import os
from dotenv import load_dotenv

load_dotenv()

memory_config = {
  "provider": "mem0",
	 "config": {"user_id": "User"},
}

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

#llm1 = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.7)

#llm3 = LLM(model="gemini/gemini-2.0-flash-exp",temperature=0.7)

# llm = LLM(model="ollama/llama3:70b", base_url="http://localhost:11434")

# llm = LLM(model="huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct", base_url="your_api_endpoint")

llm = LLM(
    model="sambanova/Llama-3.2-90B-Vision-Instruct",
    temperature=0.7
)

exa_search= EXASearchTool()
file_tool = FileReadTool()


@CrewBase
class Mas():
	"""Mas crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def market_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['market_analyst'],
			verbose=True,
			memory=True,
			llm=llm,
			tools=[exa_search, file_tool]
		)

	@agent
	def profile_assessment(self) -> Agent:
		return Agent(
			config=self.agents_config['profile_assessment'],
			verbose=True,
			memory=True,
   			llm=llm,
			tools=[file_tool]
		)

	@agent
	def skill_evaluation(self) -> Agent:
		return Agent(
			config=self.agents_config['skill_evaluation'],
			verbose=True,
			memory=True,
			llm=llm,
			tools=[file_tool]
		)
  
	@agent
	def bias_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['bias_agent'],
			verbose=True,
			memory=True,
			llm=llm
		)

	@agent
	def career_guidance(self) -> Agent:
		return Agent(
			config=self.agents_config['career_guidance'],
			verbose=True,
			memory=True,
			llm=llm,
			tools=[exa_search, file_tool]
		)

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task

	@task
	def market_analysis_task(self) -> Task:
		return Task(
			config=self.tasks_config['market_analysis_task'],
		)

	@task
	def profile_assessment_task(self) -> Task:
		return Task(
			config=self.tasks_config['profile_assessment_task']
		)

	@task
	def skill_evaluation_task(self) -> Task:
		return Task(
			config=self.tasks_config['skill_evaluation_task'],
		)
	@task
	def bias_detection_and_mitigation_task(self) -> Task:
		return Task(
			config=self.tasks_config['bias_detection_and_mitigation_task'],
		)

	@task
	def career_guidance_task(self) -> Task:
		return Task(
			config=self.tasks_config['career_guidance_task'],
			context=[self.market_analysis_task(), self.profile_assessment_task(), self.skill_evaluation_task(), self.bias_detection_and_mitigation_task()]
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Mas crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			planning=True,
			process=Process.sequential,
			# max_rpm=10,
			memory=True,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
			# manager_llm=llm,
			planning_llm=llm,
			# chat_llm=llm,
			# task_callback=True,
			output_log_file="output_log.md",
			embedder={
				"provider": "ollama",
				"config": {
        			"model": "mxbai-embed-large"
				}
			}
		)
