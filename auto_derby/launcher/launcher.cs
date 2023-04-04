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

    public class PresetInfo
    {
        public string Name
        { get; set; }

        public string Path
        { get; set; }

        public List<string> PluginFiles
        { get; set; }

        public PresetInfo()
        {
            this.Name = "None";
            this.Path = "None";
            this.PluginFiles = new List<string>();
        }
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
            this.YearOptions2 = Enum.GetValues(typeof(Year)).Cast<Year>();
            this.YearOptions3 = Enum.GetValues(typeof(Year)).Cast<Year>();
            this.MonthOptions1 = Enum.GetValues(typeof(Month)).Cast<Month>();
            this.MonthOptions2 = Enum.GetValues(typeof(Month)).Cast<Month>();
            this.MonthOptions3 = Enum.GetValues(typeof(Month)).Cast<Month>();
            this.PauseOnSpecifiedTurn1 = CalculateTurn(this.Year1, this.Month1);
            this.PauseOnSpecifiedTurn2 = CalculateTurn(this.Year2, this.Month2);
            this.PauseOnSpecifiedTurn3 = CalculateTurn(this.Year3, this.Month3);
            this.ForceRunningStyleOptions1 = Enum.GetValues(typeof(ForceRunningStyle)).Cast<ForceRunningStyle>();
            this.NurturingPresetInfoList1 = LoadPresetFiles(@"plugins\nurturing_preset");
            this.RacePresetInfoList1 = LoadPresetFiles(@"plugins\race_preset");
            DeletePresetPluginFileFromPluginDirectory(this.RacePresetInfoList1);
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


        public short PauseOnSpecifiedTurn1
        { get; set; }

        public short PauseOnSpecifiedTurn2
        { get; set; }

        public short PauseOnSpecifiedTurn3
        { get; set; }

        public Year Year1
        {
            get
            {
                var _value = (string)key.GetValue("Year1", "None");
                Year year;
                Enum.TryParse(_value, out year);
                return year;
            }
            set
            {
                key.SetValue("Year1", value.ToString());
                this.PauseOnSpecifiedTurn1 = CalculateTurn(this.Year1, this.Month1);
                OnPropertyChanged("Year1");
            }
        }

        public Year Year2
        {
            get
            {
                var _value = (string)key.GetValue("Year2", "None");
                Year year;
                Enum.TryParse(_value, out year);
                return year;
            }
            set
            {
                key.SetValue("Year2", value.ToString());
                this.PauseOnSpecifiedTurn2 = CalculateTurn(this.Year2, this.Month2);
                OnPropertyChanged("Year2");
            }
        }

        public Year Year3
        {
            get
            {
                var _value = (string)key.GetValue("Year3", "None");
                Year year;
                Enum.TryParse(_value, out year);
                return year;
            }
            set
            {
                key.SetValue("Year3", value.ToString());
                this.PauseOnSpecifiedTurn3 = CalculateTurn(this.Year3, this.Month3);
                OnPropertyChanged("Year3");
            }
        }

        public Month Month1
        {
            get
            {
                var _value = (string)key.GetValue("Month1", "None");
                Month month;
                Enum.TryParse(_value, out month);
                return month;
            }
            set
            {
                key.SetValue("Month1", value.ToString());
                this.PauseOnSpecifiedTurn1 = CalculateTurn(this.Year1, this.Month1);
                OnPropertyChanged("Month1");
            }
        }

        public Month Month2
        {
            get
            {
                var _value = (string)key.GetValue("Month2", "None");
                Month month;
                Enum.TryParse(_value, out month);
                return month;
            }
            set
            {
                key.SetValue("Month2", value.ToString());
                this.PauseOnSpecifiedTurn2 = CalculateTurn(this.Year2, this.Month2);
                OnPropertyChanged("Month2");
            }
        }

        public Month Month3
        {
            get
            {
                var _value = (string)key.GetValue("Month3", "None");
                Month month;
                Enum.TryParse(_value, out month);
                return month;
            }
            set
            {
                key.SetValue("Month3", value.ToString());
                this.PauseOnSpecifiedTurn3 = CalculateTurn(this.Year3, this.Month3);
                OnPropertyChanged("Month3");
            }
        }

        public IEnumerable<Year> YearOptions1
        { get; set; }

        public IEnumerable<Year> YearOptions2
        { get; set; }

        public IEnumerable<Year> YearOptions3
        { get; set; }

        public IEnumerable<Month> MonthOptions1
        { get; set; }

        public IEnumerable<Month> MonthOptions2
        { get; set; }

        public IEnumerable<Month> MonthOptions3
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

        public string NurturingPresetName
        {
            get
            {
                var nurturingPresetName = (string)key.GetValue("NurturingPresetName", "None");
                if(this.NurturingPresetInfoList1.Any(l => l.Name == nurturingPresetName))
                {
                    return nurturingPresetName;
                }
                return "None";
            }
            set
            {
                key.SetValue("NurturingPresetName", value);
                OnPropertyChanged("NurturingPresetName");
            }
        }

        public IEnumerable<PresetInfo> NurturingPresetInfoList1
        { get; set; }

        public string RacePresetName
        {
            get
            {
                var racePresetName = (string)key.GetValue("RacePresetName", "None");
                if(this.RacePresetInfoList1.Any(l => l.Name == racePresetName))
                {
                    return racePresetName;
                }
                return "None";
            }
            set
            {
                key.SetValue("RacePresetName", value);
                OnPropertyChanged("RacePresetName");
            }
        }

        public IEnumerable<PresetInfo> RacePresetInfoList1
        { get; set; }

        private IEnumerable<PresetInfo> LoadPresetFiles(string path)
        {
            var presetPath = Path.Combine(Environment.CurrentDirectory, path);
            var presetInfoList = new List<PresetInfo>() { new PresetInfo() };
            if(!Directory.Exists(presetPath))
            {
                return (IEnumerable<PresetInfo>)presetInfoList;
            }

            var directories = Directory.GetDirectories(presetPath);
            foreach(var dir in directories)
            {
                var pluginFiles = Directory.EnumerateFiles(dir, "*.py", SearchOption.TopDirectoryOnly);
                if(pluginFiles.Count() == 0)
                {
                    continue;
                }
                var info = new PresetInfo();
                info.Name = Path.GetFileName(dir);
                info.Path = dir;
                info.PluginFiles.AddRange(pluginFiles);
                presetInfoList.Add(info);
            }

            return (IEnumerable<PresetInfo>)presetInfoList;
        }

        private void DeletePresetPluginFileFromPluginDirectory(IEnumerable<PresetInfo> presetInfoList)
        {
            var pluginPath = Path.Combine(Environment.CurrentDirectory, "plugins");
            foreach(var racePresetInfo in presetInfoList)
            {
                foreach(var racePresetFile in racePresetInfo.PluginFiles)
                {
                    var racePluginFilePath = Path.Combine(pluginPath, Path.GetFileName(racePresetFile));
                    if(File.Exists(racePluginFilePath))
                    {
                        var isSameFile = File.ReadLines(racePluginFilePath).SequenceEqual(File.ReadLines(racePresetFile));
                        if(isSameFile)
                        {
                            File.Delete(racePluginFilePath);
                        }
                    }
                }
            }
        }
    }
}
