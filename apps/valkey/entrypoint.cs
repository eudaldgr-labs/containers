#:property PublishAot=true
#:property InvariantGlobalization=true
#:property StripSymbols=true
#:property OptimizationPreference=Size
#:property IlcOptimizationPreference=Size
#:property StackTraceSupport=false
#:property UseSystemResourceKeys=true
#:property IlcTrimMetadata=true
#:property AssemblyName=entrypoint

using System.Runtime.InteropServices;

const string AppBin = "/usr/bin/valkey-server";
const string ConfigPath = "/valkey/etc/valkey.conf";
const string DefaultConfigPath = "/usr/share/valkey/valkey.conf";

try
{
    Directory.CreateDirectory(Path.GetDirectoryName(ConfigPath)!);
    if (!File.Exists(ConfigPath))
        File.Copy(DefaultConfigPath, ConfigPath);
    Exec();
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.Message);
    Environment.Exit(1);
}

static void Exec()
{
    var args = Environment.GetCommandLineArgs();
    var defaults = ShouldRunDirectly(args) ? Array.Empty<string>() : new[] { ConfigPath };

    var argv = new string?[defaults.Length + args.Length + 1];
    argv[0] = "valkey-server";
    Array.Copy(defaults, 0, argv, 1, defaults.Length);
    Array.Copy(args, 1, argv, defaults.Length + 1, args.Length - 1);

    var result = NativeMethods.execv(AppBin, argv);
    throw new Exception($"execv({AppBin}) failed: errno {Marshal.GetLastPInvokeError()}, result {result}");
}

static bool ShouldRunDirectly(string[] args)
{
    if (args.Length < 2)
        return false;

    return args[1] is "--help" or "-h" or "--version" or "-v";
}

static class NativeMethods
{
    [DllImport("libc", SetLastError = true)]
    internal static extern int execv(string filename, string?[] argv);
}
