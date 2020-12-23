from setuptools import setup, find_packages

setup(name='Strong Poetic Password Generator',
      version='0.1',
      description='Script to generate strong passwords using PoetryDB API',
      author='Mudsill',
      packages=find_packages(),
      entry_points={
          'console_scripts': ['ppwords=ppwords.gen:gen_pword']
      }
)
