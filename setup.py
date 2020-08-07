from distutils.core import setup

setup(
  name = 'OCAT',
  packages = ['OCAT'],
  version = '0.1',
  license='MIT',
  description = 'A new single-cell analytics framework',
  author = '',
  author_email = '',
  url = 'https://github.com/bowang-lab/OCAT',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/bowang-lab/OCAT/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['RNA-SEQ', 'CLUSTERING', 'INTEGRATION'],
  install_requires=[
          'numpy',
          'pandas',
          'faiss',
          'sklearn',
          'matplotlib',
          'scipy'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)