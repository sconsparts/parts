test.Summary="Test the registry condition logic"

Test.SkipUnless(
                Condition.HasRegKey(
					HKEY_CURRENT_USER,
					["Console55\CursorSize","Console\CursorSize"],
                    "RegKey does not exist, but it should exist"
                   )
)    
                  
Test.SkipUnless(
                Condition.HasRegKey(
					HKEY_CURRENT_USER,
					["Console55\CursorSize"],
                    "This test should skip as it does not exist"
                   )
)    
