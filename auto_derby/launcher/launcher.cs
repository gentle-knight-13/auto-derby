using Microsoft.Win32;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Collections.Generic;
using System;
using System.IO;

namespace NateScarlet.AutoDerby
{
    public class JobOption
    {
        public string Label
        { get; set; }

        public string Value
        { get; set; }
    }

    public class JobOptions : ObservableCollection<JobOption>
    {
        public JobOptions()
        {
            Add(new JobOption()
            {
                Label = "Nurturing",
                Value = "nurturing",
            });
            Add(new JobOption()
            {
                Label = "Champions meeting",
                Value = "champions_meeting",
            });
            Add(new JobOption()
            {
                Label = "Team race",
                Value = "team_race",
            });
            Add(new JobOption()
            {
                Label = "Daily race: Money",
                Value = "daily_race_money",
            });
            Add(new JobOption()
            {
                Label = "Daily race: SP",
                Value = "daily_race_sp",
            });
            Add(new JobOption()
            {
                Label = "Legend race",
                Value = "legend_race",
            });
            Add(new JobOption()
            {
                Label = "Roulette derby",
                Value = "roulette_derby",
            });
        }
    }

    public enum Year : short
    {
        None = -1,
        Junior  = 0,
        Classic = 1,
        Senior = 2,
        UraFinal = 3,
    }

    public enum Month : short
    {
        None = -1,
        January_A = 1,
        January_B = 2,
        February_A = 3,
        February_B = 4,
        March_A = 5,
        March_B = 6,
        April_A = 7,
        April_B = 8,
        May_A = 9,
        May_B = 10,
        June_A = 11,
        June_B = 12,
        July_A = 13,
        July_B = 14,
        August_A = 15,
        August_B = 16,
        September_A = 17,
        September_B = 18,
        October_A = 19,
        October_B = 20,
        November_A = 21,
        November_B = 22,
        December_A = 23,
        December_B = 24,
        UraQualifying_A = 101,
        UraQualifying_B = 102,
        UraSemiFinal_A  = 103,
        UraSemiFinal_B  = 104,
        UraFinal_A      = 105,
        UraFinal_B      = 106,
        UraFinalResult  = 107,
    }

    public enum ForceRunningStyle : short
    {
        None = 0,
        Lead  = 1,
        Head = 2,
        Middle = 3,
        Last = 4,
    }

    public class DataContext : INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChangedEventHandler handler = PropertyChanged;
            if (handler != null) handler(this, new PropertyChangedEventArgs(propertyName));
        }

        private const string RegistryPath = @"Software\NateScarlet\auto-derby";

        private RegistryKey key;

        public DataContext()
        {
            this.key = Registry.CurrentUser.OpenSubKey(RegistryPath, true);
            if (this.key == null)
            {
                this.key = Registry.CurrentUser.CreateSubKey(RegistryPath);
            }

            this.JobOptions1 = new JobOptions();
            this.YearOptions1 = Enum.GetValues(typeof(Year)).Cast<Year>();
            this.MonthOptions1 = Enum.GetValues(typeof(Month)).Cast<Month>();
            this.PauseOnSpecifiedTurn = CalculateTurn(this.Year, this.Month);
            this.ForceRunningStyleOptions1 = Enum.GetValues(typeof(ForceRunningStyle)).Cast<ForceRunningStyle>();

            this.RacePluginFileInfoList1 = LoadRacePluginFiles();
            DeleteRacePluginFileFromPluginDirectory();
        }
        ~DataContext()
        {
            key.Dispose();
        }

        public string DefaultSingleModeChoicesDataPath;
        public string SingleModeChoicesDataPath
        {
            get
            {
                return (string)key.GetValue("SingleModeChoicesDataPath", DefaultSingleModeChoicesDataPath);
            }
            set
            {
                key.SetValue("SingleModeChoicesDataPath", value);
                OnPropertyChanged("SingleModeChoicesDataPath");
            }
        }

        public string DefaultPythonExecutablePath;
        public string PythonExecutablePath
        {
            get
            {
                return (string)key.GetValue("PythonExecutablePath", DefaultPythonExecutablePath);
            }
            set
            {
                key.SetValue("PythonExecutablePath", value);
                OnPropertyChanged("PythonExecutablePath");
            }
        }

        public int PauseIfRaceOrderGt
        {
            get
            {
                return (int)key.GetValue("PauseIfRaceOrderGt", 5);
            }
            set
            {
                key.SetValue("PauseIfRaceOrderGt", value, RegistryValueKind.DWord);
                OnPropertyChanged("PauseIfRaceOrderGt");
            }
        }

        public string Plugins
        {
            get
            {
                return (string)key.GetValue("Plugins", "");
            }
            set
            {
                key.SetValue("Plugins", value);
                OnPropertyChanged("Plugins");
            }
        }

        public string TargetTrainingLevels
        {
            get
            {
                return (string)key.GetValue("TargetTrainingLevels", "5,3,3,0,");
            }
            set
            {
                key.SetValue("TargetTrainingLevels", value);
                OnPropertyChanged("TargetTrainingLevels");
            }
        }

        public string ADBAddress
        {
            get
            {
                return (string)key.GetValue("ADBAddress", "");
            }
            set
            {
                key.SetValue("ADBAddress", value);
                OnPropertyChanged("ADBAddress");
            }
        }

        public bool Debug
        {
            get
            {
                return (int)key.GetValue("Debug", 1) != 0;
            }
            set
            {
                key.SetValue("Debug", value, RegistryValueKind.DWord);
                OnPropertyChanged("Debug");
            }
        }

        public bool CheckUpdate
        {
            get
            {
                return (int)key.GetValue("CheckUpdate", 1) != 0;
            }
            set
            {
                key.SetValue("CheckUpdate", value, RegistryValueKind.DWord);
                OnPropertyChanged("CheckUpdate");
            }
        }


        public string Job
        {
            get
            {
                return (string)key.GetValue("Job", "nurturing");
            }
            set
            {
                key.SetValue("Job", value);
                OnPropertyChanged("Job");
            }
        }

        public JobOptions JobOptions1
        { get; set; }


        public short PauseOnSpecifiedTurn
        { get; set; }

        public Year Year
        {
            get
            {
                var _value = (string)key.GetValue("Year", "None");
                Year year;
                Enum.TryParse(_value, out year);
                return year;
            }
            set
            {
                key.SetValue("Year", value.ToString());
                this.PauseOnSpecifiedTurn = CalculateTurn(this.Year, this.Month);
                OnPropertyChanged("Year");
            }
        }

        public Month Month
        {
            get
            {
                var _value = (string)key.GetValue("Month", "None");
                Month month;
                Enum.TryParse(_value, out month);
                return month;
            }
            set
            {
                key.SetValue("Month", value.ToString());
                this.PauseOnSpecifiedTurn = CalculateTurn(this.Year, this.Month);
                OnPropertyChanged("Month");
            }
        }

        public IEnumerable<Year> YearOptions1
        { get; set; }

        public IEnumerable<Month> MonthOptions1
        { get; set; }

        private short CalculateTurn(Year year, Month month)
        {
            if(year == Year.None || month == Month.None)
            {
                return 0;
            }

            short uraOffset = 100;
            short _year = (short)((short)year * 24);
            short _month = (short)month;
            if(year == Year.UraFinal)
            {
                if(_month > uraOffset)
                {
                    return (short)(_year + _month - uraOffset);
                }
                return (short)(_year + (short)Month.UraQualifying_A - uraOffset);
            }
            else
            {
                if(_month < uraOffset)
                {
                    return (short)(_year + _month);
                }
                return (short)(_year + (short)Month.January_A);
            }
        }


        public ForceRunningStyle ForceRunningStyle
        {
            get
            {
                var _value = (string)key.GetValue("ForceRunningStyle", "None");
                ForceRunningStyle forceRunningStyle;
                Enum.TryParse(_value, out forceRunningStyle);
                return forceRunningStyle;
            }
            set
            {
                key.SetValue("ForceRunningStyle", value.ToString());
                OnPropertyChanged("ForceRunningStyle");
            }
        }

        public IEnumerable<ForceRunningStyle> ForceRunningStyleOptions1
        { get; set; }


        public string RacePluginFileInfo
        {
            get
            {
                var racePluginFileInfo = (string)key.GetValue("RacePluginFileInfo", "None");
                if(this.RacePluginFileInfoList1.Any(l => l.Value == racePluginFileInfo))
                {
                    return racePluginFileInfo;
                }
                return "None";
            }
            set
            {
                key.SetValue("RacePluginFileInfo", value);
                OnPropertyChanged("RacePluginFileInfo");
            }
        }

        public IEnumerable<KeyValuePair<string, string>> RacePluginFileInfoList1
        { get; set; }

        private IEnumerable<KeyValuePair<string, string>> LoadRacePluginFiles()
        {
            var racePluginPath = Path.Combine(Environment.CurrentDirectory, "plugins/race_plugins");
            var racePluginFileInfoList = new List<KeyValuePair<string, string>>() { new KeyValuePair<string, string>("None", "None") };
            if(!Directory.Exists(racePluginPath))
            {
                return (IEnumerable<KeyValuePair<string, string>>)racePluginFileInfoList;
            }

            var racePluginFiles = Directory.EnumerateFiles(racePluginPath, "*.py", SearchOption.TopDirectoryOnly);
            foreach(var racePluginFile in racePluginFiles)
            {
                var fileName = Path.GetFileNameWithoutExtension(racePluginFile);
                if(racePluginFileInfoList.All(l => l.Key != fileName))
                {
                    racePluginFileInfoList.Add(
                        new KeyValuePair<string, string>(fileName, racePluginFile)
                    );
                }
            }
            return (IEnumerable<KeyValuePair<string, string>>)racePluginFileInfoList;
        }

        private void DeleteRacePluginFileFromPluginDirectory()
        {
            var pluginPath = Path.Combine(Environment.CurrentDirectory, "plugins");
            foreach(var racePluginFileInfo in this.RacePluginFileInfoList1)
            {
                var racePluginFilePath = Path.Combine(pluginPath, Path.GetFileName(racePluginFileInfo.Value));
                if(File.Exists(racePluginFilePath))
                {
                    var isSameFile = File.ReadLines(racePluginFilePath).SequenceEqual(File.ReadLines(racePluginFileInfo.Value));
                    if(isSameFile)
                    {
                        File.Delete(racePluginFilePath);
                    }
                }
            }
        }
    }
}
